import unittest
import base64
from click.testing import CliRunner
from tools.encrypt_decrypt_password_with_base32 import program_start, encryption, decryption

class TestEncryptDecryptPassword(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()

    def test_encryption(self):
        result = self.runner.invoke(program_start, ['--encrypt', 'mypassword'])
        self.assertEqual(result.exit_code, 0)
        expected_encrypted = 'NV4XAYLTON3W64TE\n'
        self.assertIn(expected_encrypted, result.output)

    def test_decryption(self):
        result = self.runner.invoke(program_start, ['--decrypt', 'NV4XAYLTON3W64TE'])
        self.assertEqual(result.exit_code, 0)
        expected_decrypted = 'mypassword\n'
        self.assertIn(expected_decrypted, result.output)

    def test_encryption_decryption_cycle(self):
        password = 'testpassword'
        encrypted = base64.b32encode(password.encode('ascii')).decode('ascii')
        decrypted = base64.b32decode(encrypted.encode('ascii')).decode('ascii')
        self.assertEqual(password, decrypted)

if __name__ == '__main__':
    unittest.main()
