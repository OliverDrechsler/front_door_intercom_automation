import unittest
from unittest.mock import patch, mock_open
from door.detect_rpi import detect_rpi


class TestDetectRpi(unittest.TestCase):
    def test_not_posix(self):
        with patch('os.name', 'nt'):
            result = detect_rpi(run_on_raspberry=False)
            self.assertFalse(result)

    def test_detect_rpi_model_file(self):
        with patch('os.name', 'posix'), \
             patch('io.open', mock_open(read_data='Raspberry Pi')) as mock_file:
            result = detect_rpi(run_on_raspberry=False)
            self.assertTrue(result)
            mock_file.assert_called_once_with('/sys/firmware/devicetree/base/model', 'r')

    def test_detect_rpi_cpuinfo_file(self):
        cpuinfo_data = (
            "Processor   : ARMv7 Processor rev 4 (v7l)\n"
            "BogoMIPS    : 38.40\n"
            "Hardware    : BCM2835\n"
        )
        with patch('os.name', 'posix'), \
             patch('io.open', mock_open(read_data=cpuinfo_data)) as mock_file:
            result = detect_rpi(run_on_raspberry=False)
            self.assertTrue(result)
            mock_file.assert_any_call('/sys/firmware/devicetree/base/model', 'r')
            mock_file.assert_called_with('/proc/cpuinfo', 'r')

    def test_detect_no_rpi_force_run(self):
        with patch('os.name', 'posix'), \
             patch('io.open', mock_open(read_data='Generic Device')) as mock_file:
            result = detect_rpi(run_on_raspberry=True)
            self.assertTrue(result)
            mock_file.assert_any_call('/sys/firmware/devicetree/base/model', 'r')
            mock_file.assert_any_call('/proc/cpuinfo', 'r')

    def test_detect_no_rpi_no_force_run(self):
        with patch('os.name', 'posix'), \
             patch('io.open', mock_open(read_data='Generic Device')) as mock_file:
            result = detect_rpi(run_on_raspberry=False)
            self.assertFalse(result)
            mock_file.assert_any_call('/sys/firmware/devicetree/base/model', 'r')
            mock_file.assert_any_call('/proc/cpuinfo', 'r')


if __name__ == '__main__':
    unittest.main()
