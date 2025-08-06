# MyelTracer
Using MyelTracer for a publication? Cite the [MyelTracer publication](https://doi.org/10.1523/ENEURO.0558-20.2021)!
- [Windows Installation](#windows-installation)
- [macOS Installation](#macOS-installation)
- [Development](#development)

![MyelTracer Screenshot](https://github.com/HarrisonAllen/MyelTracer/blob/master/readme_resources/MyelTracer.png)

## Windows installation

Requirements: Windows 10

1. Download [the Windows installer](https://github.com/HarrisonAllen/MyelTracer/releases/download/v1.3.1/MyelTracerSetup.exe)
2. Run `MyelTracerSetup.exe`
   * You may see the following warning when installing:

     ![Windows Warning](https://github.com/HarrisonAllen/MyelTracer/blob/master/readme_resources/WindowsWarning.png)
   * Click on `More info` to get the following message:

     ![Windows Warning, more info](https://github.com/HarrisonAllen/MyelTracer/blob/master/readme_resources/WindowsWarningBypass.png)
   * Finally, click `Run anyway`
3. Follow the instructions in the installer
4. MyelTracer can now be run from the start menu

## macOS installation

Requirements: macOS High Sierra (10.13) or higher

1. Download the macOS installer [the macOS installer](https://github.com/HarrisonAllen/MyelTracer/releases/download/v1.3/MyelTracer.dmg)
  
   * For macOS Sequoia (15.5) or higher: [download](https://github.com/HarrisonAllen/MyelTracer/releases/download/v1.4.0/MyelTracer.dmg)
   * For older versions, macOS High Sierra (10.13) or higher: [download](https://github.com/HarrisonAllen/MyelTracer/releases/download/v1.3/MyelTracer.dmg)
2. Open `MyelTracer.dmg`
3. Drag the `MyelTracer` icon to the `Applications` shortcut in the volume
4. MyelTracer can now be run from the `Applications` folder

You may see one of the following warnings/errors when trying to run MyelTracer:

### "Downloaded from the internet" warning

![macOS Warning](https://github.com/HarrisonAllen/MyelTracer/blob/master/readme_resources/MacOSWarning.png)

* Just click `Open` to launch MyelTracer
 
### "Damaged and can't be opened" error

![macOS Damaged](https://github.com/HarrisonAllen/MyelTracer/blob/master/readme_resources/MacOSDamaged.png)

To get around this:

1. Press `Cancel`
2. Open up the `Terminal` application
3. Copy and paste the following command  `xattr -r -d com.apple.quarantine /Applications/MyelTracer.app` then press the `enter`/`return` key on your keyboard
    * This allows the app to run despite strict code signing restrictions implemented in recent versions of macOS
4. You should now be able to launch MyelTracer

## Development

Want to customize MyelTracer to fit your needs? Here's what you need to get started.

### Setup

1. Download (or clone) this repository
2. Set up a Python 3.9 environment

    I personally use [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
    1. Create the environment by typing `conda create --name MyelTracer python=3.6`
    2. Activate the environment by typing `conda activate MyelTracer`
3. `cd` to the repository on your computer in the terminal
4. Type `pip install -r requirements.txt`
    
    * Note: using Python 3.9 requires the pro version of FBS. If you do not wish to purchase the pro version, you can install the depedencies using `requirements-python-3_6.txt` in a Python 3.6 environment

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
* For example, if you are using macOS High Sierra 10.13, then this will generate an installer that should work on macOS 10.13 and up. To create a Windows installer, you would have to repeat this process on a Windows machine.
