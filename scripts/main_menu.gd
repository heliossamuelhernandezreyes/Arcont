extends CanvasLayer
var panel:ColorRect
var title:Label
var play:Button
var camera:Button
var sensitivity:HSlider
var sensitivity_label:Label
func _ready()->void:
 layer=50;process_mode=Node.PROCESS_MODE_ALWAYS;_build();get_tree().paused=true
func _build()->void:
 panel=ColorRect.new();panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);panel.color=Color(0.025,0.035,0.055,0.94);add_child(panel)
 var box:=VBoxContainer.new();box.set_anchors_preset(Control.PRESET_CENTER);box.position=Vector2(-190,-215);box.size=Vector2(380,430);box.add_theme_constant_override("separation",12);panel.add_child(box)
 title=Label.new();title.text="ARCONT";title.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;title.add_theme_font_size_override("font_size",40);box.add_child(title)
 var subtitle:=Label.new();subtitle.text="DISTRITO DE EVACUACION 07\nPROTOTIPO TACTICO MOVIL";subtitle.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;box.add_child(subtitle)
 play=Button.new();play.text="INICIAR MISION";play.custom_minimum_size=Vector2(380,56);play.pressed.connect(_start);box.add_child(play)
 camera=Button.new();camera.text="CAMARA: TACTICAL";camera.custom_minimum_size=Vector2(380,50);camera.pressed.connect(_cycle_camera);box.add_child(camera)
 sensitivity_label=Label.new();sensitivity_label.text="SENSIBILIDAD TACTIL: 4.0";sensitivity_label.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;box.add_child(sensitivity_label)
 sensitivity=HSlider.new();sensitivity.min_value=1.5;sensitivity.max_value=9.0;sensitivity.step=0.1;sensitivity.value=4.0;sensitivity.custom_minimum_size=Vector2(380,38);sensitivity.value_changed.connect(_sensitivity_changed);box.add_child(sensitivity)
 var note:=Label.new();note.text="IZQUIERDA: mover · DERECHA: mirar\nFIRE dispara · ADS apunta · RLD recarga\nCAM: TACTICAL / CLOSE / WIDE · MENU pausa";note.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;note.add_theme_font_size_override("font_size",13);box.add_child(note)
func _start()->void:
 panel.visible=false;play.text="CONTINUAR";get_tree().paused=false
func _cycle_camera()->void:
 var p:=get_tree().get_first_node_in_group("player")
 if p and p.has_method("cycle_camera_mode"):
  p.cycle_camera_mode();camera.text="CAMARA: "+String(p.camera_mode_name())
func _sensitivity_changed(value:float)->void:
 sensitivity_label.text="SENSIBILIDAD TACTIL: %.1f"%value
 var p:=get_tree().get_first_node_in_group("player")
 if p and p.has_method("set_mobile_look_sensitivity"):p.set_mobile_look_sensitivity(value*0.001)
func show_pause()->void:
 panel.visible=true;play.text="CONTINUAR";get_tree().paused=true
func toggle_pause()->void:
 if panel.visible:_start()
 else:show_pause()
