const core = require('@actions/core');
const exec = require('@actions/exec');
const path = require('path');
const fs = require('fs');

async function runPython(script, env = {}) {
  const scriptPath = path.join(__dirname, '..', 'scripts', script);
  if (!fs.existsSync(scriptPath)) {
    core.warning(`Script ${script} not found at ${scriptPath}`);
    return;
  }
  try {
    await exec.exec('python3', [scriptPath], { env: { ...process.env, ...env } });
  } catch (err) {
    core.warning(`Script ${script} failed: ${err.message}`);
  }
}

async function capture(cmd, args, options = {}) {
  let output = '';
  await exec.exec(cmd, args, {
    ...options,
    listeners: {
      stdout: (data) => (output += data.toString()),
    },
  });
  return output;
}

async function hasCommand(cmd) {
  const { exitCode } = await exec.getExecOutput('sh', ['-c', `command -v ${cmd}`], {
    ignoreReturnCode: true,
    silent: true,
  });
  return exitCode === 0;
}

function extractZigCoverageFromHtml(html) {
  const totalMatch = html.match(/Total[^%]{0,200}([0-9]+(?:\.[0-9]+)?)%/is);
  if (totalMatch) return parseFloat(totalMatch[1]);
  const anyMatch = html.match(/([0-9]+(?:\.[0-9]+)?)%/);
  if (anyMatch) return parseFloat(anyMatch[1]);
  return null;
}

async function ensureDeps() {
  if (!(await hasCommand('mkdocs'))) {
    try {
      await exec.exec('python3', ['-m', 'pip', 'install', 'mkdocs', 'mkdocs-material']);
    } catch (err) {
      core.warning(`failed to install mkdocs: ${err.message}`);
    }
  }
}

async function run() {
  try {
    const token = core.getInput('github_token', { required: true });
    const runBench = core.getInput('run_benchmarks') !== 'false';
    const benchBranch = core.getInput('bench_branch') || 'bench-data';
    const env = {
      SITE_NAME: core.getInput('site_name') || '',
      EXTRA_DOCS: core.getInput('extra_nav_docs') !== 'false' ? 'true' : 'false',
      NAV_ORDER: core.getInput('nav_order') || 'home,reference,coverage,metrics,security,bench,docs',
      EMBED_COVERAGE: core.getInput('embed_coverage_html') !== 'false' ? 'true' : 'false',
      TOKEN: token,
      BENCH_BRANCH: benchBranch,
    };
    const failOnTestFailure = core.getInput('fail_on_test_failure') === 'true';

    await ensureDeps();

    // Go tests + coverage
    const testArgs = ['test', '-covermode=atomic', '-coverpkg', './...', '-coverprofile', 'cover.out', './...'];
    const testResult = await exec.getExecOutput('go', testArgs, { ignoreReturnCode: true });
    try {
      fs.mkdirSync('site_src', { recursive: true });
      fs.writeFileSync('site_src/tests.txt', testResult.stdout + (testResult.stderr || ''), 'utf-8');
    } catch (e) {
      core.warning(`Failed to persist test log: ${e.message}`);
    }
    if (testResult.exitCode !== 0) {
      const msg = `Go tests failed (exit ${testResult.exitCode}); proceeding with available coverage data.`;
      if (failOnTestFailure) {
        core.setFailed(msg);
        return;
      }
      core.warning(msg);
    }
    if (fs.existsSync('cover.out')) {
      try {
        await exec.exec('go', ['tool', 'cover', '-html', 'cover.out', '-o', 'cover.html']);
        const covOutput = await capture('go', ['tool', 'cover', '-func', 'cover.out']);
        const lastLine = covOutput.trim().split('\n').pop() || '';
        const pctMatch = lastLine.match(/total:\s*\(statements\)\s*([\d.]+)%/);
        const pct = pctMatch ? pctMatch[1] : '0';
        core.setOutput('coverage_percent', pct);
        fs.writeFileSync('.coverage_percent', pct, 'utf-8');
      } catch (e) {
        core.warning(`Failed to process coverage: ${e.message}`);
        core.setOutput('coverage_percent', '0');
      }
    } else {
      core.warning('cover.out not generated; setting coverage_percent=0');
      core.setOutput('coverage_percent', '0');
    }

    // Zig tests + coverage (if Zig project)
    try {
      const hasZig = (await hasCommand('zig')) && fs.existsSync('build.zig');
      if (hasZig) {
        await exec.getExecOutput('zig', ['build', 'test', '-Dcoverage'], { ignoreReturnCode: true });
        const candidates = [
          path.join('zig-out', 'coverage'),
          path.join('zig-out', 'coverage_html'),
          path.join('zig-out', 'docs', 'coverage'),
          path.join('zig-out', 'doc', 'coverage'),
        ];
        const dest = path.join('site_src' , 'zig_coverage');
        fs.mkdirSync(dest, { recursive: true });
        let copied = false;
        for (const c of candidates) {
          if (fs.existsSync(path.join(c, 'index.html'))) {
            try {
              fs.cpSync(c, dest, { recursive: true });
              copied = true;
              break;
            } catch (e) {
              core.warning(`failed to copy zig coverage from ${c}: ${e.message}`);
            }
          }
        }
        if (!copied) {
          for (const c of candidates) {
            if (fs.existsSync(path.join(c, 'coverage.html'))) {
              try {
                fs.cpSync(c, dest, { recursive: true });
                copied = true;
                break;
              } catch (e) {
                core.warning(`failed to copy zig coverage (single html) from ${c}: ${e.message}`);
              }
            }
          }
        }
        if (copied) {
          try {
            const idxPath = path.join(dest, 'index.html');
            if (fs.existsSync(idxPath)) {
              const html = fs.readFileSync(idxPath, 'utf-8');
              const pct = extractZigCoverageFromHtml(html);
              if (pct !== null) {
                const current = fs.existsSync('.coverage_percent') ? fs.readFileSync('.coverage_percent', 'utf-8').trim() : '';
                if (!current || current === '0') {
                  const str = String(pct);
                  core.setOutput('coverage_percent', str);
                  fs.writeFileSync('.coverage_percent', str, 'utf-8');
                }
              }
            }
          } catch (e) {
            core.warning(`failed to parse zig coverage percent: ${e.message}`);
          }
        }
      }
    } catch (e) {
      core.warning(`Zig coverage step failed: ${e.message}`);
    }

    if (runBench) {
      try {
        await exec.exec('bash', ['-lc', 'go test -run=^$ -bench=. -benchmem ./... | tee bench.out']);
      } catch (e) {
        await exec.exec('go', ['test', '-run=^$', '-bench=.', '-benchmem', './...']);
      }
      await runPython('update_bench.py', env);
    }
    await runPython('gen_bench_md.py', env);

    if (await hasCommand('gocyclo')) {
      process.env.METRICS = 'coverage,tests,files,loc,avg_complexity,high_complexity';
    } else {
      process.env.METRICS = 'coverage,tests,files,loc';
    }
    await runPython('collect_metrics.py', env);
    await runPython('update_metrics.py', env);
    await runPython('gen_metrics_md.py', env);

    await runPython('collect_security.py', env);
    await runPython('gen_security_md.py', env);

    await runPython('gen_coverage_md.py', env);
    await runPython('gen_site_structure.py', env);

    try {
      await exec.exec('mkdocs', ['build', '--site-dir', 'site_build']);
      core.setOutput('site_dir', 'site_build');
    } catch (err) {
      core.warning(`mkdocs not found: ${err.message}`);
    }
  } catch (error) {
    core.setFailed(error.message);
  }
}

module.exports = { run, runPython };

if (require.main === module) {
  run();
}
