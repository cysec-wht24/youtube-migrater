# This Python file uses the following encoding: utf-8
import sys
import os
import json
import shutil

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QButtonGroup,
    QFileDialog,
)
from PySide6.QtCore import QThread, QTimer

from .ui_form import Ui_MainWindow
from core.migration_worker import MigrationWorker


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        # -------------------------
        # UI SETUP
        # -------------------------
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.log_output.appendPlainText("Logs initialized")

        # Worker and thread references
        self.worker = None
        self.thread = None

        # Initial button state
        self.ui.btn_start_run.setEnabled(False)
        self.ui.btn_stop_run.setEnabled(False)

        # Disable new upload parse options until upload exists
        self.ui.group_new_upload.setEnabled(False)

        # Load existing parsed files (launchpad)
        self.load_old_parsed_files()
        
        # Load existing config if available
        self.load_existing_config()

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
        
        # -------------------------
        # DATA TAB AUTO-REFRESH
        # -------------------------
        # Connect tab change event to refresh data
        self.ui.tab_main_navigation.currentChanged.connect(self.on_tab_changed)
        
        # Set up auto-refresh timer for data tabs (every 1 second for better responsiveness)
        self.data_refresh_timer = QTimer(self)
        self.data_refresh_timer.timeout.connect(self.refresh_all_data_tabs)  # Refresh ALL tabs
        self.data_refresh_timer.start(1000)  # Refresh every 1 second
        
        # Load data tabs initially
        self.refresh_all_data_tabs()

    # --------------------------------------------------
    # CONFIG MANAGEMENT
    # --------------------------------------------------
    def load_existing_config(self):
        """Load previous configuration from data/config.json"""
        config_path = "data/config.json"
        
        if not os.path.exists(config_path):
            self.ui.log_output.appendPlainText("No previous configuration found")
            return
        
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
            
            # Restore file paths
            if config.get("client_secret_path"):
                self.ui.le_client_secret.setText(config["client_secret_path"])
            
            if config.get("html_takeout_path"):
                self.ui.le_html_takeout.setText(config["html_takeout_path"])
            
            if config.get("csv_videos_path"):
                self.ui.le_csv_videos.setText(config["csv_videos_path"])
            
            if config.get("csv_channels_path"):
                self.ui.le_csv_channels.setText(config["csv_channels_path"])
            
            # Restore limits
            if config.get("max_likes"):
                self.ui.spin_max_likes.setValue(config["max_likes"])
            
            if config.get("max_subscriptions"):
                self.ui.spin_max_subscriptions.setValue(config["max_subscriptions"])
            
            # Restore run mode
            run_mode = config.get("run_mode", "likes_then_subs")
            if run_mode == "only_likes":
                self.ui.chk_only_likes.setChecked(True)
            elif run_mode == "only_subscriptions":
                self.ui.chk_only_subscriptions.setChecked(True)
            elif run_mode == "subs_then_likes":
                self.ui.chk_subs_then_likes.setChecked(True)
            else:
                self.ui.chk_likes_then_subs.setChecked(True)
            
            self.ui.log_output.appendPlainText("✓ Previous configuration loaded")
            
        except Exception as e:
            self.ui.log_output.appendPlainText(f"⚠ Error loading config: {str(e)}")

    def save_config(self):
        """Save GUI settings to data/config.json"""
        # Determine run mode
        if self.ui.chk_only_likes.isChecked():
            run_mode = "only_likes"
        elif self.ui.chk_only_subscriptions.isChecked():
            run_mode = "only_subscriptions"
        elif self.ui.chk_likes_then_subs.isChecked():
            run_mode = "likes_then_subs"
        elif self.ui.chk_subs_then_likes.isChecked():
            run_mode = "subs_then_likes"
        else:
            run_mode = "likes_then_subs"  # default
        
        # Determine parse mode
        reparse_takeout = False
        if self.ui.chk_parse_override.isChecked():
            reparse_takeout = True
        
        config = {
            "client_secret_path": self.ui.le_client_secret.text().strip(),
            "html_takeout_path": self.ui.le_html_takeout.text().strip(),
            "csv_videos_path": self.ui.le_csv_videos.text().strip(),
            "csv_channels_path": self.ui.le_csv_channels.text().strip(),
            "max_likes": self.ui.spin_max_likes.value(),
            "max_subscriptions": self.ui.spin_max_subscriptions.value(),
            "run_mode": run_mode,
            "api_delay": 5,  # seconds between API calls
            "reparse_takeout": reparse_takeout,
            "refresh_subscriptions": False,  # Could add checkbox for this
            "refresh_channel_id": False,
        }
        
        # Copy files to data folder if they're external
        try:
            os.makedirs("data", exist_ok=True)
            
            # Copy client_secret if it's not already in data/
            client_secret_path = config["client_secret_path"]
            if client_secret_path and not client_secret_path.startswith("data/"):
                dest_path = "data/client_secret.json"
                shutil.copy2(client_secret_path, dest_path)
                config["client_secret_path"] = dest_path
                self.ui.log_output.appendPlainText(f"✓ Copied client_secret to {dest_path}")
            
            # Copy HTML takeout if it's not already in data/
            html_path = config["html_takeout_path"]
            if html_path and not html_path.startswith("data/"):
                dest_path = "data/MyActivity.html"
                shutil.copy2(html_path, dest_path)
                config["html_takeout_path"] = dest_path
                self.ui.log_output.appendPlainText(f"✓ Copied HTML takeout to {dest_path}")
            
        except Exception as e:
            self.ui.log_output.appendPlainText(f"⚠ Error copying files: {str(e)}")
        
        # Save config
        try:
            with open("data/config.json", "w") as f:
                json.dump(config, f, indent=2)
            self.ui.log_output.appendPlainText("✓ Configuration saved")
            
            # Refresh config tab if it's visible
            self.refresh_data_tab(self.ui.tab_7)
            
        except Exception as e:
            self.ui.log_output.appendPlainText(f"✗ Error saving config: {str(e)}")

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
        # Save current configuration
        self.save_config()
        self.ui.log_output.appendPlainText("\n" + "="*50)
        self.ui.log_output.appendPlainText("🚀 Starting migration...")
        self.ui.log_output.appendPlainText("="*50 + "\n")
        
        # Create worker and thread
        self.worker = MigrationWorker()
        self.thread = QThread()
        
        # Move worker to thread
        self.worker.moveToThread(self.thread)
        
        # Connect signals
        self.worker.log_message.connect(self.on_log_message)
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.finished.connect(self.on_migration_finished)
        self.worker.error_occurred.connect(self.on_migration_error)
        
        # Connect thread signals
        self.thread.started.connect(self.worker.run)
        self.thread.finished.connect(self.thread.deleteLater)
        
        # Start thread
        self.thread.start()
        
        # Update UI
        self.ui.btn_start_run.setEnabled(False)
        self.ui.btn_stop_run.setEnabled(True)

    def on_stop_clicked(self):
        if self.worker:
            self.worker.stop()
            self.ui.log_output.appendPlainText("\n⏸ Stop requested by user...")

    # --------------------------------------------------
    # WORKER SIGNAL HANDLERS
    # --------------------------------------------------
    def on_log_message(self, message):
        """Handle log messages from worker"""
        self.ui.log_output.appendPlainText(message)

    def on_progress_updated(self, current, total, operation_type):
        """Handle progress updates from worker"""
        percentage = int((current / total) * 100) if total > 0 else 0
        
        if operation_type == "parsing":
            self.ui.log_output.appendPlainText(
                f"   Parsing: {current}/{total} entries ({percentage}%)"
            )
        elif operation_type == "subscriptions":
            self.ui.log_output.appendPlainText(
                f"   Subscriptions: {current}/{total} ({percentage}%)"
            )
        elif operation_type == "likes":
            self.ui.log_output.appendPlainText(
                f"   Likes: {current}/{total} ({percentage}%)"
            )

    def on_migration_finished(self):
        """Handle migration completion"""
        self.ui.log_output.appendPlainText("\n" + "="*50)
        self.ui.log_output.appendPlainText("✓ Migration process finished")
        self.ui.log_output.appendPlainText("="*50 + "\n")
        
        # Update UI
        self.ui.btn_start_run.setEnabled(True)
        self.ui.btn_stop_run.setEnabled(False)
        
        # Clean up thread
        if self.thread:
            self.thread.quit()
            self.thread.wait()
        
        # Update parse data state (in case files were deleted)
        self.update_parse_data_mode_state()
        
        # Refresh all data tabs to show updated files
        self.refresh_all_data_tabs()

    def on_migration_error(self, error_msg):
        """Handle migration errors"""
        self.ui.log_output.appendPlainText("\n" + "="*50)
        self.ui.log_output.appendPlainText(f"✗ Error: {error_msg}")
        self.ui.log_output.appendPlainText("="*50 + "\n")
        
        # Update UI
        self.ui.btn_start_run.setEnabled(True)
        self.ui.btn_stop_run.setEnabled(False)
        
        # Clean up thread
        if self.thread:
            self.thread.quit()
            self.thread.wait()

    # --------------------------------------------------
    # DATA / STATE INITIALIZATION
    # --------------------------------------------------
    def load_old_parsed_files(self):
        """Load list of old parsed files from data folder"""
        self.old_parsed_files = []
        
        # Check if parsed_activity.json exists
        if os.path.exists("data/parsed_activity.json"):
            try:
                with open("data/parsed_activity.json", "r") as f:
                    data = json.load(f)
                    if any(data.values()):  # Has non-empty data
                        self.old_parsed_files.append("data/parsed_activity.json")
            except Exception:
                pass

        self.ui.cmb_old_parsed_files.clear()

        if not self.old_parsed_files:
            self.ui.chk_use_old_parsed.setEnabled(False)
            self.ui.cmb_old_parsed_files.setEnabled(False)
            self.ui.cmb_old_parsed_files.addItem(
                "No stored parsed data available"
            )
        else:
            self.ui.chk_use_old_parsed.setEnabled(True)
            self.ui.cmb_old_parsed_files.setEnabled(True)
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
    # PARSE / DATA STATE
    # --------------------------------------------------
    def has_active_parsed_data(self):
        return bool(self.old_parsed_files)

    def update_parse_data_mode_state(self):
        # Reload old parsed files
        self.load_old_parsed_files()
        
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

        # Check if user has provided data to work with
        has_data = (
            self.is_html_upload_active() 
            or self.is_csv_upload_active() 
            or self.has_active_parsed_data()
        )

        can_start = (
            client_secret_ok
            and limits_ok
            and run_mode_ok
            and has_data
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
        self.ui.log_output.appendPlainText("Client Secret cleared")

    # --------------------------------------------------
    # DATA TAB MANAGEMENT
    # --------------------------------------------------
    def on_tab_changed(self, index):
        """Called when user switches tabs"""
        # Get the current tab widget
        current_tab = self.ui.tab_main_navigation.widget(index)
        
        # Refresh data if we're on a data tab (tab2-tab7)
        if current_tab in [
            self.ui.tab_2,  # parsed_activity
            self.ui.tab_3,  # progress
            self.ui.tab_4,  # token
            self.ui.tab_5,  # api_derived
            self.ui.tab_6,  # client_secret
            self.ui.tab_7,  # user_config
        ]:
            self.refresh_data_tab(current_tab)
    
    def refresh_current_data_tab(self):
        """Refresh currently visible data tab"""
        current_index = self.ui.tab_main_navigation.currentIndex()
        current_tab = self.ui.tab_main_navigation.widget(current_index)
        self.refresh_data_tab(current_tab)
    
    def refresh_all_data_tabs(self):
        """Refresh all data tabs"""
        for tab in [
            self.ui.tab_2,  # parsed_activity
            self.ui.tab_3,  # progress
            self.ui.tab_4,  # token
            self.ui.tab_5,  # api_derived
            self.ui.tab_6,  # client_secret
            self.ui.tab_7,  # user_config
        ]:
            self.refresh_data_tab(tab)
    
    def refresh_data_tab(self, tab):
        """Refresh content of a specific data tab"""
        try:
            # Map tabs to their editors and files
            tab_mapping = {
                self.ui.tab_2: ("data/parsed_activity.json", self.ui.editor_parsed_activity),
                self.ui.tab_3: ("data/progress.json", self.ui.editor_progress),
                self.ui.tab_4: ("data/token.json", self.ui.editor_token),
                self.ui.tab_5: ("data/api_derived.json", self.ui.editor_api_derived),
                self.ui.tab_6: ("data/client_secret.json", self.ui.editor_client_secret),
                self.ui.tab_7: ("data/config.json", self.ui.editor_user_config),
            }
            
            if tab not in tab_mapping:
                return
            
            file_path, editor = tab_mapping[tab]
            
            # Check if file exists
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    # Pretty print JSON
                    try:
                        json_data = json.loads(content)
                        formatted_content = json.dumps(json_data, indent=2)
                        
                        # Only update if content has changed (prevents flickering)
                        current_text = editor.toPlainText()
                        if current_text != formatted_content:
                            # Save cursor position
                            cursor = editor.textCursor()
                            position = cursor.position()
                            
                            editor.setPlainText(formatted_content)
                            
                            # Restore cursor position if possible
                            if position < len(formatted_content):
                                cursor.setPosition(position)
                                editor.setTextCursor(cursor)
                    except json.JSONDecodeError:
                        # Not valid JSON, display as-is
                        if editor.toPlainText() != content:
                            editor.setPlainText(content)
                    
                except Exception as e:
                    error_msg = f"Error reading file: {str(e)}"
                    if editor.toPlainText() != error_msg:
                        editor.setPlainText(error_msg)
            else:
                not_found_msg = f"File not found: {file_path}\n\nThis file will be created when needed."
                if editor.toPlainText() != not_found_msg:
                    editor.setPlainText(not_found_msg)
        
        except Exception as e:
            pass  # Silently fail if tab doesn't exist


# --------------------------------------------------
# APPLICATION ENTRY POINT
# --------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec())