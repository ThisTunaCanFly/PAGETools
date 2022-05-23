from pagetools.src.line2page.Line2Page import Line2Page

import logging
from pathlib import Path
import click
import time
import multiprocessing
from multiprocessing import Semaphore


@click.command("line2page", help="Merges line images and text to combined image with PAGE XML annotation")
@click.option('-c', '--creator', default='user', help='Creator tag for PAGE XML')
@click.option('-s', '--source-folder', required=True, help='Path to images and GT')
@click.option('-i', '--image-folder', default='', help='Path to images')
@click.option('-gt', '--gt-folder', default='', help='Path to GT')
@click.option('-d', '--dest-folder', default=Path(Path.cwd(), 'merged'), help='Path to merge objects')
@click.option('-e', '--ext', default='.bin.png', help='Image extension')
@click.option('-p', '--pred', default=False, type=bool, help='Set flag to also store .pred.txt')
@click.option('-l', '--lines', default=20, type=click.IntRange(min=0,clamp=True), help='Lines per page')
@click.option('-ls', '--line-spacing', default=5, type=click.IntRange(min=0,clamp=True),
              help='Line spacing in pixel; (top, bottom, left, right)')
@click.option('-b', '--border', nargs=4, default=(10, 10, 10, 10), type=click.IntRange(min=0,clamp=True),
              help='Border (in pixel)')
@click.option('--debug', default='20', type=click.Choice(['10', '20', '30', '40', '50']),
              help='Sets the level of feedback to receive: DEBUG=10, INFO=20, WARNING=30, ERROR=40, CRITICAL=50')
@click.option('--threads', default=16, type=click.IntRange(min=1,clamp=True), help='Thread count to be used')
@click.option('--xml-schema', default='19', type=click.Choice(['17', '19']),
              help='Sets the year of the xml-Schema to be used')
def line2page_cli(creator, source_folder, image_folder, gt_folder, dest_folder, ext, pred, lines, line_spacing, border,
                  debug, threads, xml_schema):
    image_path = source_folder if not image_folder else image_folder
    gt_path = source_folder if not gt_folder else gt_folder

    logging.basicConfig(level=int(debug))
    log = logging.getLogger(__name__)
    tic = time.perf_counter()
    opt_obj = Line2Page(creator, source_folder, image_path, gt_path, dest_folder, ext, pred, lines, line_spacing,
                        border, debug, threads, xml_schema)
    opt_obj.match_files()
    pages = list(opt_obj.chunks(opt_obj.matches, opt_obj.lines))
    pages = opt_obj.name_pages(pages)

    i = 0
    processes = []
    concurrency = opt_obj.threads
    log.info(f" Currently using {str(concurrency)} Thread(s)")
    # click.echo(f"Currently using {str(concurrency)} Thread(s)")
    sema = Semaphore(concurrency)
    with click.progressbar(pages, label=f"Processing {len(pages)} Pages") as bar_processing:
        for page in bar_processing:
            sema.acquire()
            process = multiprocessing.Process(target=opt_obj.make_page, args=(page, sema,))
            processes.append(process)
            process.start()

    with click.progressbar(processes, label=f"Finishing {len(processes)}Pages:") as bar_finishing:
        for process in bar_finishing:
            process.join()
    toc = time.perf_counter()
    log.info(f" Finished merging in {toc - tic:0.4f} seconds")
    # click.echo(f"\nFinished merging in {toc - tic:0.4f} seconds")
    log.info(f" Pages have been stored at {str(opt_obj.dest_folder)}")
    # click.echo(f"\nPages have been stored at {str(opt_obj.dest_folder)}")


if __name__ == '__main__':
    line2page_cli()
