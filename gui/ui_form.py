# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'form.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMenuBar, QPlainTextEdit, QPushButton,
    QScrollArea, QSizePolicy, QSpinBox, QStatusBar,
    QTabWidget, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.setEnabled(True)
        MainWindow.resize(750, 450)
        MainWindow.setMinimumSize(QSize(750, 450))
        MainWindow.setMaximumSize(QSize(750, 450))
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.btn_start_run = QPushButton(self.centralwidget)
        self.btn_start_run.setObjectName(u"btn_start_run")

        self.verticalLayout.addWidget(self.btn_start_run)

        self.btn_stop_run = QPushButton(self.centralwidget)
        self.btn_stop_run.setObjectName(u"btn_stop_run")

        self.verticalLayout.addWidget(self.btn_stop_run)

        self.tab_main_navigation = QTabWidget(self.centralwidget)
        self.tab_main_navigation.setObjectName(u"tab_main_navigation")
        self.tab_main_navigation.setIconSize(QSize(16, 16))
        self.tab1 = QWidget()
        self.tab1.setObjectName(u"tab1")
        self.verticalLayout_2 = QVBoxLayout(self.tab1)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.scrollArea = QScrollArea(self.tab1)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, -910, 683, 1155))
        self.verticalLayout_3 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.home_scroll_content = QWidget(self.scrollAreaWidgetContents)
        self.home_scroll_content.setObjectName(u"home_scroll_content")
        self.formLayout = QFormLayout(self.home_scroll_content)
        self.formLayout.setObjectName(u"formLayout")
        self.group_csv_upload = QGroupBox(self.home_scroll_content)
        self.group_csv_upload.setObjectName(u"group_csv_upload")
        self.verticalLayout_12 = QVBoxLayout(self.group_csv_upload)
        self.verticalLayout_12.setObjectName(u"verticalLayout_12")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.lbl_csv_channels = QLabel(self.group_csv_upload)
        self.lbl_csv_channels.setObjectName(u"lbl_csv_channels")

        self.horizontalLayout_3.addWidget(self.lbl_csv_channels)

        self.le_csv_channels = QLineEdit(self.group_csv_upload)
        self.le_csv_channels.setObjectName(u"le_csv_channels")
        self.le_csv_channels.setReadOnly(True)

        self.horizontalLayout_3.addWidget(self.le_csv_channels)

        self.btn_browse_csv_channels = QPushButton(self.group_csv_upload)
        self.btn_browse_csv_channels.setObjectName(u"btn_browse_csv_channels")

        self.horizontalLayout_3.addWidget(self.btn_browse_csv_channels)


        self.verticalLayout_12.addLayout(self.horizontalLayout_3)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.lbl_csv_videos = QLabel(self.group_csv_upload)
        self.lbl_csv_videos.setObjectName(u"lbl_csv_videos")

        self.horizontalLayout.addWidget(self.lbl_csv_videos)

        self.le_csv_videos = QLineEdit(self.group_csv_upload)
        self.le_csv_videos.setObjectName(u"le_csv_videos")
        self.le_csv_videos.setReadOnly(True)

        self.horizontalLayout.addWidget(self.le_csv_videos)

        self.btn_browse_csv_videos = QPushButton(self.group_csv_upload)
        self.btn_browse_csv_videos.setObjectName(u"btn_browse_csv_videos")

        self.horizontalLayout.addWidget(self.btn_browse_csv_videos)


        self.verticalLayout_12.addLayout(self.horizontalLayout)

        self.btn_clear_csv_upload = QPushButton(self.group_csv_upload)
        self.btn_clear_csv_upload.setObjectName(u"btn_clear_csv_upload")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_clear_csv_upload.sizePolicy().hasHeightForWidth())
        self.btn_clear_csv_upload.setSizePolicy(sizePolicy)

        self.verticalLayout_12.addWidget(self.btn_clear_csv_upload)


        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.group_csv_upload)

        self.group_client_secret_upload = QGroupBox(self.home_scroll_content)
        self.group_client_secret_upload.setObjectName(u"group_client_secret_upload")
        self.verticalLayout_19 = QVBoxLayout(self.group_client_secret_upload)
        self.verticalLayout_19.setObjectName(u"verticalLayout_19")
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.lbl_client_secret = QLabel(self.group_client_secret_upload)
        self.lbl_client_secret.setObjectName(u"lbl_client_secret")

        self.horizontalLayout_4.addWidget(self.lbl_client_secret)

        self.le_client_secret = QLineEdit(self.group_client_secret_upload)
        self.le_client_secret.setObjectName(u"le_client_secret")
        self.le_client_secret.setReadOnly(True)

        self.horizontalLayout_4.addWidget(self.le_client_secret)

        self.btn_browse_client_secret = QPushButton(self.group_client_secret_upload)
        self.btn_browse_client_secret.setObjectName(u"btn_browse_client_secret")

        self.horizontalLayout_4.addWidget(self.btn_browse_client_secret)


        self.verticalLayout_19.addLayout(self.horizontalLayout_4)

        self.btn_clear_client_secret = QPushButton(self.group_client_secret_upload)
        self.btn_clear_client_secret.setObjectName(u"btn_clear_client_secret")
        sizePolicy.setHeightForWidth(self.btn_clear_client_secret.sizePolicy().hasHeightForWidth())
        self.btn_clear_client_secret.setSizePolicy(sizePolicy)

        self.verticalLayout_19.addWidget(self.btn_clear_client_secret)


        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.group_client_secret_upload)

        self.group_max_limits = QGroupBox(self.home_scroll_content)
        self.group_max_limits.setObjectName(u"group_max_limits")
        self.verticalLayout_13 = QVBoxLayout(self.group_max_limits)
        self.verticalLayout_13.setObjectName(u"verticalLayout_13")
        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.lbl_max_like_limit = QLabel(self.group_max_limits)
        self.lbl_max_like_limit.setObjectName(u"lbl_max_like_limit")

        self.horizontalLayout_5.addWidget(self.lbl_max_like_limit)

        self.spin_max_likes = QSpinBox(self.group_max_limits)
        self.spin_max_likes.setObjectName(u"spin_max_likes")
        self.spin_max_likes.setMaximum(100000)

        self.horizontalLayout_5.addWidget(self.spin_max_likes)


        self.verticalLayout_13.addLayout(self.horizontalLayout_5)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.lbl_max_sub_limit = QLabel(self.group_max_limits)
        self.lbl_max_sub_limit.setObjectName(u"lbl_max_sub_limit")

        self.horizontalLayout_6.addWidget(self.lbl_max_sub_limit)

        self.spin_max_subscriptions = QSpinBox(self.group_max_limits)
        self.spin_max_subscriptions.setObjectName(u"spin_max_subscriptions")
        self.spin_max_subscriptions.setMaximum(100000)

        self.horizontalLayout_6.addWidget(self.spin_max_subscriptions)


        self.verticalLayout_13.addLayout(self.horizontalLayout_6)


        self.formLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.group_max_limits)

        self.group_parse_options = QGroupBox(self.home_scroll_content)
        self.group_parse_options.setObjectName(u"group_parse_options")
        self.verticalLayout_15 = QVBoxLayout(self.group_parse_options)
        self.verticalLayout_15.setObjectName(u"verticalLayout_15")
        self.group_new_upload = QGroupBox(self.group_parse_options)
        self.group_new_upload.setObjectName(u"group_new_upload")
        self.verticalLayout_16 = QVBoxLayout(self.group_new_upload)
        self.verticalLayout_16.setObjectName(u"verticalLayout_16")
        self.chk_parse_append = QCheckBox(self.group_new_upload)
        self.chk_parse_append.setObjectName(u"chk_parse_append")

        self.verticalLayout_16.addWidget(self.chk_parse_append)

        self.chk_parse_override = QCheckBox(self.group_new_upload)
        self.chk_parse_override.setObjectName(u"chk_parse_override")

        self.verticalLayout_16.addWidget(self.chk_parse_override)

        self.chk_parse_separate = QCheckBox(self.group_new_upload)
        self.chk_parse_separate.setObjectName(u"chk_parse_separate")

        self.verticalLayout_16.addWidget(self.chk_parse_separate)


        self.verticalLayout_15.addWidget(self.group_new_upload)

        self.group_default_options = QGroupBox(self.group_parse_options)
        self.group_default_options.setObjectName(u"group_default_options")
        self.formLayout_2 = QFormLayout(self.group_default_options)
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.chk_use_active_parsed = QCheckBox(self.group_default_options)
        self.chk_use_active_parsed.setObjectName(u"chk_use_active_parsed")

        self.formLayout_2.setWidget(0, QFormLayout.ItemRole.SpanningRole, self.chk_use_active_parsed)

        self.chk_use_old_parsed = QCheckBox(self.group_default_options)
        self.chk_use_old_parsed.setObjectName(u"chk_use_old_parsed")

        self.formLayout_2.setWidget(1, QFormLayout.ItemRole.LabelRole, self.chk_use_old_parsed)

        self.cmb_old_parsed_files = QComboBox(self.group_default_options)
        self.cmb_old_parsed_files.setObjectName(u"cmb_old_parsed_files")
        self.cmb_old_parsed_files.setEnabled(False)

        self.formLayout_2.setWidget(1, QFormLayout.ItemRole.FieldRole, self.cmb_old_parsed_files)


        self.verticalLayout_15.addWidget(self.group_default_options)


        self.formLayout.setWidget(5, QFormLayout.ItemRole.LabelRole, self.group_parse_options)

        self.group_html_upload = QGroupBox(self.home_scroll_content)
        self.group_html_upload.setObjectName(u"group_html_upload")
        self.verticalLayout_18 = QVBoxLayout(self.group_html_upload)
        self.verticalLayout_18.setObjectName(u"verticalLayout_18")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.lbl_html_takeout = QLabel(self.group_html_upload)
        self.lbl_html_takeout.setObjectName(u"lbl_html_takeout")

        self.horizontalLayout_2.addWidget(self.lbl_html_takeout)

        self.le_html_takeout = QLineEdit(self.group_html_upload)
        self.le_html_takeout.setObjectName(u"le_html_takeout")
        self.le_html_takeout.setReadOnly(True)

        self.horizontalLayout_2.addWidget(self.le_html_takeout)

        self.btn_browse_html_takeout = QPushButton(self.group_html_upload)
        self.btn_browse_html_takeout.setObjectName(u"btn_browse_html_takeout")

        self.horizontalLayout_2.addWidget(self.btn_browse_html_takeout)


        self.verticalLayout_18.addLayout(self.horizontalLayout_2)

        self.btn_clear_html_upload = QPushButton(self.group_html_upload)
        self.btn_clear_html_upload.setObjectName(u"btn_clear_html_upload")
        sizePolicy.setHeightForWidth(self.btn_clear_html_upload.sizePolicy().hasHeightForWidth())
        self.btn_clear_html_upload.setSizePolicy(sizePolicy)

        self.verticalLayout_18.addWidget(self.btn_clear_html_upload)


        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.group_html_upload)

        self.group_what_to_run = QGroupBox(self.home_scroll_content)
        self.group_what_to_run.setObjectName(u"group_what_to_run")
        self.verticalLayout_14 = QVBoxLayout(self.group_what_to_run)
        self.verticalLayout_14.setObjectName(u"verticalLayout_14")
        self.chk_only_likes = QCheckBox(self.group_what_to_run)
        self.chk_only_likes.setObjectName(u"chk_only_likes")

        self.verticalLayout_14.addWidget(self.chk_only_likes)

        self.chk_only_subscriptions = QCheckBox(self.group_what_to_run)
        self.chk_only_subscriptions.setObjectName(u"chk_only_subscriptions")

        self.verticalLayout_14.addWidget(self.chk_only_subscriptions)

        self.chk_likes_then_subs = QCheckBox(self.group_what_to_run)
        self.chk_likes_then_subs.setObjectName(u"chk_likes_then_subs")

        self.verticalLayout_14.addWidget(self.chk_likes_then_subs)

        self.chk_subs_then_likes = QCheckBox(self.group_what_to_run)
        self.chk_subs_then_likes.setObjectName(u"chk_subs_then_likes")

        self.verticalLayout_14.addWidget(self.chk_subs_then_likes)


        self.formLayout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.group_what_to_run)

        self.group_save_config = QGroupBox(self.home_scroll_content)
        self.group_save_config.setObjectName(u"group_save_config")
        self.verticalLayout_17 = QVBoxLayout(self.group_save_config)
        self.verticalLayout_17.setObjectName(u"verticalLayout_17")
        self.chk_save_config = QCheckBox(self.group_save_config)
        self.chk_save_config.setObjectName(u"chk_save_config")
        self.chk_save_config.setChecked(False)

        self.verticalLayout_17.addWidget(self.chk_save_config)


        self.formLayout.setWidget(6, QFormLayout.ItemRole.LabelRole, self.group_save_config)


        self.verticalLayout_3.addWidget(self.home_scroll_content)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout_2.addWidget(self.scrollArea)

        self.tab_main_navigation.addTab(self.tab1, "")
        self.tab2 = QWidget()
        self.tab2.setObjectName(u"tab2")
        self.verticalLayout_5 = QVBoxLayout(self.tab2)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.data_editing_tabs = QTabWidget(self.tab2)
        self.data_editing_tabs.setObjectName(u"data_editing_tabs")
        self.data_editing_tabs.setStyleSheet(u"font: 10pt \"Segoe UI\";")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.verticalLayout_6 = QVBoxLayout(self.tab_2)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.editor_parsed_activity = QPlainTextEdit(self.tab_2)
        self.editor_parsed_activity.setObjectName(u"editor_parsed_activity")
        self.editor_parsed_activity.setStyleSheet(u"font-family: Consolas, \"Courier New\", monospace;\n"
"font-size: 11pt;")

        self.verticalLayout_6.addWidget(self.editor_parsed_activity)

        self.data_editing_tabs.addTab(self.tab_2, "")
        self.tab_3 = QWidget()
        self.tab_3.setObjectName(u"tab_3")
        self.verticalLayout_7 = QVBoxLayout(self.tab_3)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.editor_progress = QPlainTextEdit(self.tab_3)
        self.editor_progress.setObjectName(u"editor_progress")
        self.editor_progress.setStyleSheet(u"font-family: Consolas, \"Courier New\", monospace;\n"
"font-size: 11pt;")

        self.verticalLayout_7.addWidget(self.editor_progress)

        self.data_editing_tabs.addTab(self.tab_3, "")
        self.tab_5 = QWidget()
        self.tab_5.setObjectName(u"tab_5")
        self.verticalLayout_9 = QVBoxLayout(self.tab_5)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.editor_api_derived = QPlainTextEdit(self.tab_5)
        self.editor_api_derived.setObjectName(u"editor_api_derived")
        self.editor_api_derived.setStyleSheet(u"font-family: Consolas, \"Courier New\", monospace;\n"
"font-size: 11pt;")

        self.verticalLayout_9.addWidget(self.editor_api_derived)

        self.data_editing_tabs.addTab(self.tab_5, "")
        self.tab_4 = QWidget()
        self.tab_4.setObjectName(u"tab_4")
        self.verticalLayout_8 = QVBoxLayout(self.tab_4)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.editor_token = QPlainTextEdit(self.tab_4)
        self.editor_token.setObjectName(u"editor_token")
        self.editor_token.setStyleSheet(u"font-family: Consolas, \"Courier New\", monospace;\n"
"font-size: 11pt;")

        self.verticalLayout_8.addWidget(self.editor_token)

        self.data_editing_tabs.addTab(self.tab_4, "")
        self.tab_6 = QWidget()
        self.tab_6.setObjectName(u"tab_6")
        self.verticalLayout_10 = QVBoxLayout(self.tab_6)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.editor_client_secret = QPlainTextEdit(self.tab_6)
        self.editor_client_secret.setObjectName(u"editor_client_secret")
        self.editor_client_secret.setStyleSheet(u"font-family: Consolas, \"Courier New\", monospace;\n"
"font-size: 11pt;")

        self.verticalLayout_10.addWidget(self.editor_client_secret)

        self.data_editing_tabs.addTab(self.tab_6, "")
        self.tab_7 = QWidget()
        self.tab_7.setObjectName(u"tab_7")
        self.verticalLayout_11 = QVBoxLayout(self.tab_7)
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.editor_user_config = QPlainTextEdit(self.tab_7)
        self.editor_user_config.setObjectName(u"editor_user_config")
        font = QFont()
        font.setFamilies([u"Consolas"])
        font.setPointSize(11)
        font.setBold(False)
        font.setItalic(False)
        self.editor_user_config.setFont(font)
        self.editor_user_config.setStyleSheet(u"font-family: Consolas, \"Courier New\", monospace;\n"
"font-size: 11pt;")

        self.verticalLayout_11.addWidget(self.editor_user_config)

        self.data_editing_tabs.addTab(self.tab_7, "")

        self.verticalLayout_5.addWidget(self.data_editing_tabs)

        self.tab_main_navigation.addTab(self.tab2, "")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.verticalLayout_4 = QVBoxLayout(self.tab)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.log_output = QPlainTextEdit(self.tab)
        self.log_output.setObjectName(u"log_output")
        self.log_output.setReadOnly(True)

        self.verticalLayout_4.addWidget(self.log_output)

        self.tab_main_navigation.addTab(self.tab, "")

        self.verticalLayout.addWidget(self.tab_main_navigation)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 750, 25))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        self.tab_main_navigation.setCurrentIndex(0)
        self.data_editing_tabs.setCurrentIndex(3)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.btn_start_run.setText(QCoreApplication.translate("MainWindow", u"Start", None))
        self.btn_stop_run.setText(QCoreApplication.translate("MainWindow", u"Stop", None))
        self.group_csv_upload.setTitle(QCoreApplication.translate("MainWindow", u"CSV Uploads", None))
        self.lbl_csv_channels.setText(QCoreApplication.translate("MainWindow", u"CSV File (Channels)", None))
        self.le_csv_channels.setPlaceholderText("")
        self.btn_browse_csv_channels.setText(QCoreApplication.translate("MainWindow", u"Browse", None))
        self.lbl_csv_videos.setText(QCoreApplication.translate("MainWindow", u"CSV File (Videos)", None))
        self.btn_browse_csv_videos.setText(QCoreApplication.translate("MainWindow", u"Browse", None))
        self.btn_clear_csv_upload.setText(QCoreApplication.translate("MainWindow", u"Clear Upload", None))
        self.group_client_secret_upload.setTitle(QCoreApplication.translate("MainWindow", u"Client Secret (OAuth)", None))
        self.lbl_client_secret.setText(QCoreApplication.translate("MainWindow", u"Client Secret File (JSON)", None))
        self.btn_browse_client_secret.setText(QCoreApplication.translate("MainWindow", u"Browse", None))
        self.btn_clear_client_secret.setText(QCoreApplication.translate("MainWindow", u"Clear Upload", None))
        self.group_max_limits.setTitle(QCoreApplication.translate("MainWindow", u"Execution Limits", None))
        self.lbl_max_like_limit.setText(QCoreApplication.translate("MainWindow", u"Max likes per run:", None))
#if QT_CONFIG(tooltip)
        self.spin_max_likes.setToolTip(QCoreApplication.translate("MainWindow", u"0", None))
#endif // QT_CONFIG(tooltip)
        self.lbl_max_sub_limit.setText(QCoreApplication.translate("MainWindow", u"Max subscriptions per run:", None))
#if QT_CONFIG(tooltip)
        self.spin_max_subscriptions.setToolTip(QCoreApplication.translate("MainWindow", u"0", None))
#endif // QT_CONFIG(tooltip)
        self.group_parse_options.setTitle(QCoreApplication.translate("MainWindow", u"Parse and Data Selection", None))
        self.group_new_upload.setTitle(QCoreApplication.translate("MainWindow", u"Choose (New Upload)", None))
        self.chk_parse_append.setText(QCoreApplication.translate("MainWindow", u"Parse new file and append data to active storage", None))
        self.chk_parse_override.setText(QCoreApplication.translate("MainWindow", u"Parse new file and override active data (are you sure?)", None))
        self.chk_parse_separate.setText(QCoreApplication.translate("MainWindow", u"Parse new file and use separately", None))
        self.group_default_options.setTitle(QCoreApplication.translate("MainWindow", u"Default Options", None))
        self.chk_use_active_parsed.setText(QCoreApplication.translate("MainWindow", u"Use the already present active parsed data", None))
        self.chk_use_old_parsed.setText(QCoreApplication.translate("MainWindow", u"Use old parsed stored data", None))
        self.group_html_upload.setTitle(QCoreApplication.translate("MainWindow", u"HTML Upload", None))
        self.lbl_html_takeout.setText(QCoreApplication.translate("MainWindow", u"HTML Takeout File ", None))
        self.btn_browse_html_takeout.setText(QCoreApplication.translate("MainWindow", u"Browse", None))
        self.btn_clear_html_upload.setText(QCoreApplication.translate("MainWindow", u"Clear Upload", None))
        self.group_what_to_run.setTitle(QCoreApplication.translate("MainWindow", u"What to Run", None))
        self.chk_only_likes.setText(QCoreApplication.translate("MainWindow", u"Run only Likes", None))
        self.chk_only_subscriptions.setText(QCoreApplication.translate("MainWindow", u"Run only Subscriptions", None))
        self.chk_likes_then_subs.setText(QCoreApplication.translate("MainWindow", u"Likes \u2192 then Subscriptions", None))
        self.chk_subs_then_likes.setText(QCoreApplication.translate("MainWindow", u"Subscriptions \u2192 then Likes", None))
        self.group_save_config.setTitle(QCoreApplication.translate("MainWindow", u"Save Configuration", None))
        self.chk_save_config.setText(QCoreApplication.translate("MainWindow", u"Save configuration for next launch", None))
        self.tab_main_navigation.setTabText(self.tab_main_navigation.indexOf(self.tab1), QCoreApplication.translate("MainWindow", u"Home", None))
        self.data_editing_tabs.setTabText(self.data_editing_tabs.indexOf(self.tab_2), QCoreApplication.translate("MainWindow", u"parsed_activity", None))
        self.data_editing_tabs.setTabText(self.data_editing_tabs.indexOf(self.tab_3), QCoreApplication.translate("MainWindow", u"progress", None))
        self.data_editing_tabs.setTabText(self.data_editing_tabs.indexOf(self.tab_5), QCoreApplication.translate("MainWindow", u"api_derived", None))
        self.data_editing_tabs.setTabText(self.data_editing_tabs.indexOf(self.tab_4), QCoreApplication.translate("MainWindow", u"token", None))
        self.data_editing_tabs.setTabText(self.data_editing_tabs.indexOf(self.tab_6), QCoreApplication.translate("MainWindow", u"client_secret", None))
        self.data_editing_tabs.setTabText(self.data_editing_tabs.indexOf(self.tab_7), QCoreApplication.translate("MainWindow", u"user_config", None))
        self.tab_main_navigation.setTabText(self.tab_main_navigation.indexOf(self.tab2), QCoreApplication.translate("MainWindow", u"Data", None))
        self.tab_main_navigation.setTabText(self.tab_main_navigation.indexOf(self.tab), QCoreApplication.translate("MainWindow", u"Logs", None))
    # retranslateUi

