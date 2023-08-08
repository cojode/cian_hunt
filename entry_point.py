import cian_offers_parser
import scrolling_unit
import click

dump_path = "data/links_list.pickle"


def main():
    links = cian_offers_parser.load_data(dump_path)
    print(f"Loaded {len(links)} offers")

    click.confirm("Start searching?", abort=True)
    scrolling_unit.scrolling_process(links)


if __name__ == '__main__':
    main()
