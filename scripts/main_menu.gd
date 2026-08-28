extends CanvasLayer
var panel:ColorRect
var title:Label
var play:Button
var resume:Button
var camera:Button
func _ready()->void:
 layer=50;_build();get_tree().paused=true
func _build()->void:
 panel=ColorRect.new();panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);panel.color=Color(0.025,0.035,0.055,0.94);add_child(panel)
 var box:=VBoxContainer.new();box.set_anchors_preset(Control.PRESET_CENTER);box.position=Vector2(-170,-150);box.size=Vector2(340,300);box.add_theme_constant_override("separation",18);panel.add_child(box)
 title=Label.new();title.text="ARCONT";title.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;title.add_theme_font_size_override("font_size",42);box.add_child(title)
 var subtitle:=Label.new();subtitle.text="DISTRITO DE EVACUACION 07\nPROTOTIPO TACTICO";subtitle.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;box.add_child(subtitle)
 play=Button.new();play.text="INICIAR MISION";play.custom_minimum_size=Vector2(340,54);play.pressed.connect(_start);box.add_child(play)
 camera=Button.new();camera.text="CAMARA: TACTICAL";camera.custom_minimum_size=Vector2(340,48);camera.pressed.connect(_cycle_camera);box.add_child(camera)
 var note:=Label.new();note.text="Arrastra el lado derecho para mirar";note.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;box.add_child(note)
func _start()->void:panel.visible=false;get_tree().paused=false
func _cycle_camera()->void:
 var p:=get_tree().get_first_node_in_group("player");if p and p.has_method("cycle_camera_mode"):p.cycle_camera_mode();camera.text="CAMARA: "+String(p.camera_mode_name())
func show_pause()->void:panel.visible=true;play.text="CONTINUAR";get_tree().paused=true
