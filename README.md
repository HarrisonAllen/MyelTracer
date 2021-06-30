# MyelTracer
- [Windows Installation](#windows-installation)
- [MacOS Installation](#macos-installation)
- [Development](#development)

## Windows installation

Requirements: Windows 10

1. Download [the Windows installer](https://github.com/HarrisonAllen/MyelTracer/raw/master/Windows/MyelTracerSetup.exe)
2. Run `MyelTracerSetup.exe`
   * You may see the following warning when installing:

     ![Windows Warning](https://github.com/HarrisonAllen/MyelTracer/blob/master/readme_resources/WindowsWarning.png)
   * Click on `More info` to get the following message:

     ![Windows Warning, more info](https://github.com/HarrisonAllen/MyelTracer/blob/master/readme_resources/WindowsWarningBypass.png)
   * Finally, click `Run anyway`
3. Follow the instructions in the installer
4. MyelTracer can now be run from the start menu

## MacOS installation

Requirements: MacOS High Sierra (10.13) or higher

1. Download [the MacOS installer](https://github.com/HarrisonAllen/MyelTracer/raw/master/Mac/MyelTracer.dmg)
2. Open `MyelTracer.dmg`
3. Drag the `MyelTracer` icon to the `Applications` shortcut in the volume
4. MyelTracer can now be run from the `Applications` folder
   * You may see the following warning the first time you run the application:

     ![MacOS Warning](https://github.com/HarrisonAllen/MyelTracer/blob/master/readme_resources/MacOSWarning.png)
   * Just click `Open` to launch MyelTracer

## Development

Want to customize MyelTracer to fit your needs? Here's what you need to get started.

### Setup

1. Download (or clone) this repository
2. Set up a Python 3.6 environment
    * I personally use [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
    1. Create the environment by typing `conda create --name MyelTracer python=3.6`
    2. Activate the environment by typing `conda activate MyelTracer`
3. `cd` to the repository on your computer in the terminal
4. Type `pip install -r requirements.txt`

### Editing the software

All of the code is stored in `SourceCode/src/main/python/main.py`. This is the file you should edit.

The software GUI is designed with [PyQt5](https://pypi.org/project/PyQt5/).

Image processing is done using [OpenCV](https://opencv.org/).

Software is packaged with [fman build system](https://build-system.fman.io/).

### Running the software

1. In the `SourceCode` directory, type `fbs run`

### Packaging the software

1. In the `SourceCode` directory, type `fbs freeze`
2. Type `fbs installer`

This will generate a standalone installer for the operating system that you are currently using. 
* For example, if you are using MacOS High Sierra 10.13, then this will generate an installer that should work on MacOS 10.13 and up. To create a Windows installer, you would have to repeat this process on a Windows machine.
