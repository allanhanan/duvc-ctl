# duvc-ctl

Windows DirectShow UVC camera control library with C++, Python and CLI surfaces for programmatic camera control on Windows.  

## Highlights

- UVC camera enumeration and control.  
- PTZ (Pan/Tilt/Zoom) operations.  
- Camera properties (exposure, focus, iris).  
- Video properties (brightness, contrast, saturation).  
- C/C++ core, Python bindings, and CLI tooling for multiple workflows.  

## Native C/C++ Reference

- See the auto-generated reference: [C/C++ API (Doxygen)](../doxygen/html/index.html)

```{toctree}
:maxdepth: 2
:caption: Getting Started

user-guide/quickstart
user-guide/installation
user-guide/migration
```

```{toctree}
:maxdepth: 2
:caption: API Reference

api/c/index
api/cpp/index
api/cli/index
api/python/index
```

```{toctree}
:maxdepth: 2
:caption: Examples

examples/cli-examples
examples/cpp-examples
examples/python-examples
```

## Future plans
### Current version plans
- Rust 
- vcpkg
- winget(hopefully i dont need a certificate im broke TwT)
- Node.js
- Go
- choco
- whatever else exists

### Next version updates
- figure out a way for connetion pooling but still be thread safe
- i forgor :skull:

[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](README.md)
[![Language](https://img.shields.io/badge/C%2B%2B-17-blue.svg)](src/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-green.svg)](pyproject.toml)
![Pepy Total Downloads](https://img.shields.io/pepy/dt/duvc-ctl?style=flat&label=pip%20installs)

If you like what I do, check this out!
[<img src="https://www.buymeacoffee.com/assets/img/custom_images/yellow_img.png" alt="Buy Me A Coffee">](https://www.buymeacoffee.com/allanhanan)

## Indices and Tables

- {ref}`genindex`
- {ref}`modindex`
- {ref}`search`
