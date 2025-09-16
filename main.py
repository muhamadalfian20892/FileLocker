import wx
import sys
from gui_main import MainWindow
from core_settings import Settings

def main():
    app = wx.App()
    settings = Settings()
    frame = MainWindow(settings)
    frame.Show()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--register':
        from core_paths import register_shell_integration
        register_shell_integration()
    
    app.MainLoop()

if __name__ == '__main__':
    main()