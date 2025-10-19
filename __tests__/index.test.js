const path = require('path');
const core = require('@actions/core');
const exec = require('@actions/exec');
const { runPython } = require('../src/index');

jest.mock('@actions/core');
jest.mock('@actions/exec');

describe('runPython', () => {
  beforeEach(() => {
    exec.exec.mockReset().mockResolvedValue(0);
    core.warning.mockReset();
  });

  test('executes existing script', async () => {
    await runPython('gen_site_structure.py', {});
    expect(exec.exec).toHaveBeenCalled();
    const scriptPath = exec.exec.mock.calls[0][1][0];
    const expected = path.join(process.cwd(), 'scripts', 'gen_site_structure.py');
    expect(scriptPath).toBe(expected);
  });

  test('warns when script missing', async () => {
    await runPython('missing_script.py', {});
    expect(core.warning).toHaveBeenCalled();
    expect(exec.exec).not.toHaveBeenCalled();
  });
});
