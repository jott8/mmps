from scan import scan
from plotting.plotting import generate_graphs


def main() -> None:
    scan_result = scan()

    if (scan_result):
        print('Scan completed successfully\n')

        print('Started graph generation\n')
        generate_graphs()
        print('Graph generation done.')

    else:
        print('Something went wrong...')


if __name__ == '__main__':
    main()
