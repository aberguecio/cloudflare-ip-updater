import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class CronTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copy(Path(__file__).with_name("install-cron.sh"), self.root)
        self.state = self.root / "crontab.txt"
        self.state.write_text("*/5 * * * * docker exec nextcloud php cron.php\n")
        bindir = self.root / "bin"
        bindir.mkdir()
        scripts = {
            "crontab": '#!/bin/sh\nif [ "$1" = "-l" ]; then\n'
                       '  if [ "${READ_ERROR:-}" = yes ]; then echo "permission denied" >&2; exit 1; fi\n'
                       '  cat "$CRON_STATE"\nelse cat > "$CRON_STATE"; fi\n',
            "flock": "#!/bin/sh\nexit 0\n",
        }
        for name, body in scripts.items():
            f = bindir / name
            f.write_text(body)
            f.chmod(0o755)
        self.env = {**os.environ, "PATH": str(bindir) + ":" + os.environ["PATH"], "CRON_STATE": str(self.state)}

    def install(self):
        return subprocess.run(["bash", str(self.root / "install-cron.sh")], env=self.env, capture_output=True)

    def test_repeat_install_preserves_unrelated_jobs_and_one_managed_entry(self):
        legacy = f"*/10 * * * * cd {self.root}/ && python3 cloudflare-redirect-rules.py >> log 2>&1\n"
        self.state.write_text(self.state.read_text() + legacy)
        self.assertEqual(self.install().returncode, 0)
        self.assertEqual(self.install().returncode, 0)
        result = self.state.read_text()
        self.assertIn("docker exec nextcloud", result)
        self.assertEqual(result.count("cloudflare-redirect-rules.py"), 1)
        self.assertIn("*/10 * * * *", result)
        self.assertIn("/usr/bin/flock -n", result)

    def test_read_failure_never_replaces_existing_schedule(self):
        before = self.state.read_bytes()
        self.env["READ_ERROR"] = "yes"
        self.assertNotEqual(self.install().returncode, 0)
        self.assertEqual(self.state.read_bytes(), before)
