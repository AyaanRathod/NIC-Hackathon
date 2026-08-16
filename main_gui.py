from nicegui import ui


def main():
    ui.label('Hello World!')


if __name__ in {'__main__', '__mp_main__'}:
	main()
	ui.run()