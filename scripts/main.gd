extends Node2D

const PLAYER_SPEED := 320.0
const PLAYER_RADIUS := 22.0
const GRID_SIZE := 64.0

var player_position := Vector2(640, 360)

func _ready() -> void:
	queue_redraw()

func _process(delta: float) -> void:
	var direction := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	player_position += direction * PLAYER_SPEED * delta
	var viewport_size := get_viewport_rect().size
	player_position.x = clamp(player_position.x, PLAYER_RADIUS, viewport_size.x - PLAYER_RADIUS)
	player_position.y = clamp(player_position.y, PLAYER_RADIUS, viewport_size.y - PLAYER_RADIUS)
	queue_redraw()

func _draw() -> void:
	var viewport_size := get_viewport_rect().size
	_draw_grid(viewport_size)
	_draw_player()
	_draw_hud()

func _draw_grid(size: Vector2) -> void:
	var grid_color := Color(0.12, 0.15, 0.22, 0.45)
	var x := 0.0
	while x <= size.x:
		draw_line(Vector2(x, 0), Vector2(x, size.y), grid_color, 1.0)
		x += GRID_SIZE
	var y := 0.0
	while y <= size.y:
		draw_line(Vector2(0, y), Vector2(size.x, y), grid_color, 1.0)
		y += GRID_SIZE

func _draw_player() -> void:
	draw_circle(player_position, PLAYER_RADIUS + 6.0, Color(0.10, 0.18, 0.28, 0.9))
	draw_circle(player_position, PLAYER_RADIUS, Color(0.35, 0.82, 1.0, 1.0))
	draw_circle(player_position, 7.0, Color(0.92, 0.98, 1.0, 1.0))

func _draw_hud() -> void:
	var font := ThemeDB.fallback_font
	draw_string(font, Vector2(32, 48), "ARCONT // PROTOTIPO 0.1", HORIZONTAL_ALIGNMENT_LEFT, -1, 24, Color(0.9, 0.95, 1.0))
	draw_string(font, Vector2(32, 78), "WASD / flechas para moverte", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color(0.62, 0.7, 0.82))
