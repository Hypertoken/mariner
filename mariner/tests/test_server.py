from unittest import TestCase
from unittest.mock import patch, MagicMock, Mock

from pyexpect import expect
from starlette.testclient import TestClient

from mariner.file_formats.ctb import CTBFile
from mariner.mars import ElegooMars, PrinterState, PrintStatus
from mariner.server import app


class MarinerServerTest(TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

        self.printer_mock = Mock(spec=ElegooMars)
        self.printer_patcher = patch("mariner.server.ElegooMars")
        printer_constructor_mock = self.printer_patcher.start()
        printer_constructor_mock.return_value = self.printer_mock
        self.printer_mock.__enter__ = Mock(return_value=self.printer_mock)
        self.printer_mock.__exit__ = Mock(return_value=None)

        self.ctb_file_mock = Mock(spec=CTBFile)
        self.ctb_file_mock.layer_count = 19
        self.ctb_file_mock.print_time_secs = 200
        self.ctb_file_mock.end_byte_offset_by_layer = [
            (i + 1) * 6 for i in range(0, self.ctb_file_mock.layer_count)
        ]
        self.ctb_file_patcher = patch("mariner.server.CTBFile")
        ctb_file_class_mock = self.ctb_file_patcher.start()
        ctb_file_class_mock.read.return_value = self.ctb_file_mock

    def tearDown(self) -> None:
        self.printer_patcher.stop()
        self.ctb_file_patcher.stop()

    def test_print_status_while_printing(self) -> None:
        self.printer_mock.get_selected_file.return_value = "foobar.ctb"
        self.printer_mock.get_print_status.return_value = PrintStatus(
            state=PrinterState.PRINTING,
            current_byte=42,
            total_bytes=120,
        )
        response = self.client.get("/api/print_status")
        expect(response.json()).to_equal(
            {
                "state": "PRINTING",
                "selected_file": "foobar.ctb",
                "progress": 35.0,
                "layer_count": 19,
                "current_layer": 7,
                "print_time_secs": 200,
            }
        )

    def test_print_status_when_paused(self) -> None:
        self.printer_mock.get_selected_file.return_value = "foobar.ctb"
        self.printer_mock.get_print_status.return_value = PrintStatus(
            state=PrinterState.PAUSED,
            current_byte=42,
            total_bytes=120,
        )
        response = self.client.get("/api/print_status")
        expect(response.json()).to_equal(
            {
                "state": "PAUSED",
                "selected_file": "foobar.ctb",
                "progress": 35.0,
                "layer_count": 19,
                "current_layer": 7,
                "print_time_secs": 200,
            }
        )

    def test_print_status_while_starting_print(self) -> None:
        self.printer_mock.get_selected_file.return_value = "foobar.ctb"
        self.printer_mock.get_print_status.return_value = PrintStatus(
            state=PrinterState.STARTING_PRINT,
            current_byte=0,
            total_bytes=120,
        )
        response = self.client.get("/api/print_status")
        expect(response.json()).to_equal(
            {
                "state": "STARTING_PRINT",
                "selected_file": "foobar.ctb",
                "progress": 0.0,
                "layer_count": 19,
                "current_layer": 1,
                "print_time_secs": 200,
            }
        )

    def test_print_status_while_idle(self) -> None:
        self.printer_mock.get_selected_file.return_value = "foobar.ctb"
        self.printer_mock.get_print_status.return_value = PrintStatus(
            state=PrinterState.IDLE,
            current_byte=0,
            total_bytes=0,
        )
        response = self.client.get("/api/print_status")
        expect(response.json()).to_equal(
            {
                "state": "IDLE",
                "selected_file": "foobar.ctb",
                "progress": 0.0,
            }
        )

    @patch("mariner.server.os.listdir", return_value=["a.ctb", "b.ctb"])
    def test_list_files(self, _list_dir_mock: MagicMock) -> None:
        response = self.client.get("/api/list_files")
        expect(response.json()).to_equal(
            {
                "files": [
                    {"filename": "a.ctb", "print_time_secs": 200},
                    {"filename": "b.ctb", "print_time_secs": 200},
                ],
            }
        )

    def test_command_start_printing(self) -> None:
        response = self.client.post(
            "/api/printer/command/start_print?filename=foobar.ctb"
        )
        expect(response.json()).to_equal({"success": True})
        self.printer_mock.start_printing.assert_called_once_with("foobar.ctb")

    def test_command_pause_print(self) -> None:
        response = self.client.post("/api/printer/command/pause_print")
        expect(response.json()).to_equal({"success": True})
        self.printer_mock.pause_printing.assert_called_once_with()

    def test_command_resume_print(self) -> None:
        response = self.client.post("/api/printer/command/resume_print")
        expect(response.json()).to_equal({"success": True})
        self.printer_mock.resume_printing.assert_called_once_with()

    def test_command_cancel_print(self) -> None:
        response = self.client.post("/api/printer/command/cancel_print")
        expect(response.json()).to_equal({"success": True})
        self.printer_mock.stop_printing.assert_called_once_with()

    def test_command_reboot(self) -> None:
        response = self.client.post("/api/printer/command/reboot")
        expect(response.json()).to_equal({"success": True})
        self.printer_mock.reboot.assert_called_once_with()
