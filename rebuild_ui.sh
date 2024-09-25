#cd ~/bin/QtDesigner/
source ~/bin/QtDesigner/.venv/bin/activate
pyuic6 -o main_ui.py ui/main.ui
pyuic6 -o FieldUnits/select_tag_dialog_ui.py ui/select_tag_dialog.ui
pyuic6 -o new_project_dialog_ui.py ui/new_project.ui
pyuic6 -o plc_dialog_ui.py ui/add_plc.ui
