from cx_Freeze import setup, Executable
 
exe = Executable(
    script='AoS-ServerBrowser.py',
    base="Win32GUI",
    icon='diamonds.ico',
    compress = True,
    copyDependentFiles = True

  #  targetDir = 'AoS-ServerBrowser'
    )
includefiles = ['diamonds.png','diamonds.ico','README.txt','LICENSE.txt']
setup(
    name = '5 of Diamonds',
    description = 'Ace of Spades Server Browser',
    version = '1.3',
    options = {'build_exe': {'include_files':includefiles}},     
    executables = [exe]
)
