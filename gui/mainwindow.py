# This Python file uses the following encoding: utf-8
import sys

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QButtonGroup,
    QFileDialog,
)

from .ui_form import Ui_MainWindow


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        # -------------------------
        # UI SETUP
        # -------------------------
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.log_output.appendPlainText("Logs initialized")

        # Initial button state
        self.ui.btn_start_run.setEnabled(False)
        self.ui.btn_stop_run.setEnabled(False)

        # Disable new upload parse options until upload exists
        self.ui.group_new_upload.setEnabled(False)

        # Load existing parsed files (launchpad)
        self.load_old_parsed_files()

        # -------------------------
        # RUN MODE BUTTON GROUP
        # -------------------------
        self.run_mode_group = QButtonGroup(self)
        self.run_mode_group.setExclusive(True)

        self.run_mode_group.addButton(self.ui.chk_only_likes)
        self.run_mode_group.addButton(self.ui.chk_only_subscriptions)
        self.run_mode_group.addButton(self.ui.chk_likes_then_subs)
        self.run_mode_group.addButton(self.ui.chk_subs_then_likes)

        self.ui.chk_likes_then_subs.setChecked(True)

        # -------------------------
        # NEW UPLOAD PARSE MODE GROUP
        # -------------------------
        self.new_upload_group = QButtonGroup(self)
        self.new_upload_group.setExclusive(True)

        self.new_upload_group.addButton(self.ui.chk_parse_append)
        self.new_upload_group.addButton(self.ui.chk_parse_override)
        self.new_upload_group.addButton(self.ui.chk_parse_separate)

        # -------------------------
        # SIGNAL CONNECTIONS
        # -------------------------
        self.ui.btn_clear_csv_upload.clicked.connect(self.clear_csv_upload)
        self.ui.btn_clear_html_upload.clicked.connect(self.clear_html_upload)
        self.ui.btn_clear_client_secret.clicked.connect(self.clear_client_secret)

        self.ui.btn_start_run.clicked.connect(self.on_start_clicked)
        self.ui.btn_stop_run.clicked.connect(self.on_stop_clicked)

        # Browse buttons
        self.ui.btn_browse_client_secret.clicked.connect(
            lambda: self.browse_file(
                self.ui.le_client_secret,
                "Select Client Secret JSON",
                "JSON Files (*.json)",
            )
        )

        self.ui.btn_browse_csv_videos.clicked.connect(
            lambda: self.browse_file(
                self.ui.le_csv_videos,
                "Select Videos CSV",
                "CSV Files (*.csv)",
            )
        )

        self.ui.btn_browse_csv_channels.clicked.connect(
            lambda: self.browse_file(
                self.ui.le_csv_channels,
                "Select Channels CSV",
                "CSV Files (*.csv)",
            )
        )

        self.ui.btn_browse_html_takeout.clicked.connect(
            lambda: self.browse_file(
                self.ui.le_html_takeout,
                "Select YouTube HTML Takeout",
                "HTML Files (*.html)",
            )
        )

        # Start-button state triggers
        self.ui.le_client_secret.textChanged.connect(self.update_start_stop_state)

        self.ui.spin_max_likes.valueChanged.connect(self.update_start_stop_state)
        self.ui.spin_max_subscriptions.valueChanged.connect(
            self.update_start_stop_state
        )

        for btn in self.run_mode_group.buttons():
            btn.toggled.connect(self.update_start_stop_state)

        for btn in self.new_upload_group.buttons():
            btn.toggled.connect(self.update_start_stop_state)

        self.ui.chk_use_active_parsed.toggled.connect(self.update_start_stop_state)
        self.ui.chk_use_old_parsed.toggled.connect(self.update_start_stop_state)

        # Initialize states
        self.update_upload_exclusivity()
        self.update_parse_data_mode_state()
        self.update_start_stop_state()

    # --------------------------------------------------
    # BROWSING FUNCTION
    # --------------------------------------------------
    def browse_file(self, target_line_edit, caption, file_filter):
        file_path, _ = QFileDialog.getOpenFileName(
            self, caption, "", file_filter
        )

        if not file_path:
            return

        target_line_edit.setText(file_path)
        self.ui.log_output.appendPlainText(f"Selected file: {file_path}")

        self.update_upload_exclusivity()
        self.update_parse_data_mode_state()
        self.update_start_stop_state()

    # --------------------------------------------------
    # START / STOP
    # --------------------------------------------------
    def on_start_clicked(self):
        self.ui.log_output.appendPlainText("Run started")

        self.ui.btn_start_run.setEnabled(False)
        self.ui.btn_stop_run.setEnabled(True)

    def on_stop_clicked(self):
        self.ui.log_output.appendPlainText("Run stopped")

        self.ui.btn_start_run.setEnabled(True)
        self.ui.btn_stop_run.setEnabled(False)

    # --------------------------------------------------
    # DATA / STATE INITIALIZATION
    # --------------------------------------------------
    def load_old_parsed_files(self):
        self.old_parsed_files = []  # launchpad

        self.ui.cmb_old_parsed_files.clear()

        if not self.old_parsed_files:
            self.ui.chk_use_old_parsed.setEnabled(False)
            self.ui.cmb_old_parsed_files.setEnabled(False)
            self.ui.cmb_old_parsed_files.addItem(
                "No stored parsed data available"
            )
        else:
            self.ui.chk_use_old_parsed.setEnabled(True)
            self.ui.cmb_old_parsed_files.setEnabled(False)
            self.ui.cmb_old_parsed_files.addItems(self.old_parsed_files)

    # --------------------------------------------------
    # UPLOAD STATE
    # --------------------------------------------------
    def is_csv_upload_active(self):
        return bool(
            self.ui.le_csv_videos.text().strip()
            or self.ui.le_csv_channels.text().strip()
        )

    def is_html_upload_active(self):
        return bool(self.ui.le_html_takeout.text().strip())

    def update_upload_exclusivity(self):
        csv_active = self.is_csv_upload_active()
        html_active = self.is_html_upload_active()

        self.ui.group_html_upload.setEnabled(not csv_active)
        self.ui.group_csv_upload.setEnabled(not html_active)

    # --------------------------------------------------
    # PARSE / DATA STATE (LAUNCHPAD)
    # --------------------------------------------------
    def has_active_parsed_data(self):
        return bool(self.old_parsed_files)

    def update_parse_data_mode_state(self):
        upload_exists = (
            self.is_csv_upload_active() or self.is_html_upload_active()
        )
        parsed_exists = self.has_active_parsed_data()

        self.ui.group_new_upload.setEnabled(upload_exists)
        self.ui.group_default_options.setEnabled(parsed_exists)

    # --------------------------------------------------
    # START BUTTON VALIDATION
    # --------------------------------------------------
    def update_start_stop_state(self):
        client_secret_ok = bool(self.ui.le_client_secret.text().strip())

        limits_ok = (
            self.ui.spin_max_likes.value() > 0
            and self.ui.spin_max_subscriptions.value() > 0
        )

        run_mode_ok = any(
            btn.isChecked() for btn in self.run_mode_group.buttons()
        )

        parse_ok = (
            any(btn.isChecked() for btn in self.new_upload_group.buttons())
            or self.ui.chk_use_active_parsed.isChecked()
            or self.ui.chk_use_old_parsed.isChecked()
        )

        can_start = (
            client_secret_ok
            and limits_ok
            and run_mode_ok
            and parse_ok
            and not self.ui.btn_stop_run.isEnabled()
        )

        self.ui.btn_start_run.setEnabled(can_start)

    # --------------------------------------------------
    # CLEAR / RESET
    # --------------------------------------------------
    def clear_csv_upload(self):
        self.ui.le_csv_videos.clear()
        self.ui.le_csv_channels.clear()
        self.update_upload_exclusivity()
        self.update_parse_data_mode_state()
        self.update_start_stop_state()
        self.ui.log_output.appendPlainText("CSV upload cleared")

    def clear_html_upload(self):
        self.ui.le_html_takeout.clear()
        self.update_upload_exclusivity()
        self.update_parse_data_mode_state()
        self.update_start_stop_state()
        self.ui.log_output.appendPlainText("HTML upload cleared")

    def clear_client_secret(self):
        self.ui.le_client_secret.clear()
        self.update_start_stop_state()
        self.ui.log_output.appendPlainText("Client Secret upload cleared")


# --------------------------------------------------
# APPLICATION ENTRY POINT
# --------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec())
