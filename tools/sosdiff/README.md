# sosdiff

The sosdiff python tool takes sos reports from two systems, and compares them. It can be very helpful to find differences between a "good" and a "bad" system, in terms of an operational or performance problem. 

Or maybe just to validate two systems are actually setup in a very similar fashion.

The goal after extensive internal testing will be to merge this into the mainline sos RPM code. 

## Usage

Run it with `python -m sosdiff`:

``` bash
$ python -m sosdiff -h
usage: sosdiff [-h] [-d] [-o] [-c] [-v] dir1 dir2

sosdiff - Compare 2 sosreports

positional arguments:
  dir1            First sos report directory
  dir2            Second sos report directory

optional arguments:
  -h, --help      show this help message and exit
  -d, --detail    Run with extensive sosreport detailed checking (default:
                  False)
  -o, --override  Run despite mis-matched OL version or CPU architecture
                  (default: False)
  -c, --color     Always output color escape sequences (default: False)
  -v, --version   show program's version number and exit
```

### Runtime dependencies

- `python3`

## Contributing

This project welcomes contributions from the community. Before submitting a
pull request, please [review our contribution guide](./CONTRIBUTING.md)

## Security

Please consult the [security guide](./SECURITY.md) for our responsible security
vulnerability disclosure process

## License

sosdiff is licensed under [GPLv2](LICENSE.txt).

