#cd ~/bin/QtDesigner/
#source ~/bin/QtDesigner/.venv/bin/activate
pyuic6 -o main_ui.py ui/main.ui
pyuic6 -o FieldUnits/select_tag_dialog_ui.py ui/select_tag_dialog.ui
pyuic6 -o new_project_dialog_ui.py ui/new_project.ui
pyuic6 -o plc_dialog_ui.py ui/add_plc.ui
pyuic6 -o comissioning_helper/helper_window_ui.py ui/commisionning_helper.ui
pyuic6 -o comissioning_helper/config_helper_dialog_ui.py ui/config_helper.ui
pyuic6 -o comissioning_helper/form_tab2_widget_ui.py ui/FormTab2.ui
# ControlNet debug tool
pyuic6 -o cn_diag_tool/cn_diag_tool_ui.tmp ui/cn_diag_tool.main.ui
sed 's/:\/asset\//asset:/g' cn_diag_tool/cn_diag_tool_ui.tmp > cn_diag_tool/cn_diag_tool_ui.py
rm cn_diag_tool/cn_diag_tool_ui.tmp

pyuic6 -o cn_diag_tool/floating_table_ui.py.tmp ui/FloatingTable.ui
sed 's/:\/asset\//asset:/g' cn_diag_tool/floating_table_ui.py.tmp > cn_diag_tool/floating_table_ui.py
rm cn_diag_tool/floating_table_ui.py.tmp

#rcc -g python -o resources.py asset/res.qrc