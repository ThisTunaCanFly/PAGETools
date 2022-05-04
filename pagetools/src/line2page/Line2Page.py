# Nachfragen
import lxml

# keep this
import glob
from pathlib import Path
import sys
from PIL import Image
from xml.etree.ElementTree import Element, SubElement
from xml.etree import ElementTree
from datetime import datetime
from xml.dom import minidom


class Line2Page:
    """Object, which includes the meta data
    source, image_folder, gt_folder, dest_folder are Path objects
    """

    def __init__(self, creator, source, i_f, gt_f, dest, ext, pred, lines, spacing, border, debug, threads):
        self.creator = creator
        self.source = Path(self.check_absolute(source))
        if not self.source.is_dir():
            raise Exception("Source folder " + str(self.source.resolve()) + " does not exist")
        self.image_folder = Path(self.check_absolute(i_f))
        if not i_f == source:
            self.check_dest(self.image_folder)
        self.gt_folder = Path(self.check_absolute(gt_f))
        if not gt_f == source:
            self.check_dest(self.gt_folder)
        self.dest_folder = self.check_dest(Path(self.check_absolute(dest)))
        self.ext = ext
        self.pred = pred
        self.lines = lines
        self.line_spacing = spacing
        self.border = border
        self.debug = debug
        self.threads = threads

        # List of all images in the folder with the desired extension
        self.imgList = [f for f in sorted(glob.glob(str(self.image_folder) + '/*' + self.ext))]
        self.gtList = []
        self.nameList = []
        self.matches = []
        self.spacer = 5
        self.img_ext = '.nrm.png'
        self.xmlSchemaLocation = \
            'http://schema.primaresearch.org/PAGE/gts/pagecontent/2017-07-15 ' \
            'http://schema.primaresearch.org/PAGE/gts/pagecontent/2017-07-15/pagecontent.xsd'

        # self.print_self()


    @staticmethod
    def check_dest(dest: Path):
        # remove
        print("Checking destination")

        """Checks if the destination is legitimate and creates directory, if it does not exist yet"""
        if not dest.exists():
            print(str(dest) + " dir not found, creating directory")
            # dest.parent.chmod(stat.S_IWRITE)
            dest.expanduser()
            Path.mkdir(dest, parents=True, exist_ok=True)
        # Needed?
        # if not dest.endswith(os.path.sep):
        #    dest += os.path.sep
        return dest

    @staticmethod
    def check_absolute(folder: str):
        """Checks if the given Path is absolute, if not: adds cwd()"""
        if folder.startswith("/"):
            return folder
        else:
            return str(Path.cwd()) + "/" + folder

    @staticmethod
    def strip_path(path: Path):
        """extracts the basename of path"""
        # check if it needs to be a path
        return path.name

    @staticmethod
    def get_text(file):
        # remove
        # print("get_text(" + file + ")")
        """extracts the text from inside the file"""
        with open(file, 'r') as read_file:
            data = read_file.read().rstrip()
            return data

    @staticmethod
    def chunks(lst, n):
        # remove
        # print("chunks(" + str(lst) + ", " + str(n) + ")")
        """Yields successive n-sized chunks from lst"""
        for i in range(0, len(lst), n):
            yield lst[i: i + n]

    @staticmethod
    def name_pages(pages):
        # remove
        # print("name_pages(" + str(pages) + ")")
        """
        returns a list of all objects in pages with pagename followed by a 4-digit pagenumber
        removed iterative
        """
        page_with_name = []
        pages_with_name = []
        page_iterator = 0
        for page in pages:
            page_iterator += 1
            name = str(page_iterator).zfill(4)
            page_with_name.append(page)
            page_with_name.append(name)
            pages_with_name.append(page_with_name.copy())
            page_with_name.clear()
        # print("Pages: " + str(pages_with_name)) # remove
        return pages_with_name

    @staticmethod
    def progress(count, total, status='.'):
        # remove
        # print("progress bar")

        """displays a progress bar"""
        bar_len = 60
        filled_len = int(round(bar_len * count / float(total)))
        percents = round(100.0 * count / float(total), 1)
        bar = '█' * filled_len + '_' * (bar_len - filled_len)
        sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
        sys.stdout.flush()

    @staticmethod
    def prettify(elem):
        # remove
        # print("prettify")

        """Return a pretty-printed XML string for the Element.
        """
        rough_string = ElementTree.tostring(elem, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml("  ")

    def make_page(self, page_with_name, semaphore):
        # remove
        # print("make_page(" + str(page_with_name) + ", " + str(semaphore) + ")")

        merged = self.merge_images(page_with_name[0])
        merged.save(str(self.dest_folder) + "/" + self.strip_path(Path(page_with_name[1])) + self.img_ext)
        merged.close()
        xml_tree = self.build_xml(page_with_name[0], page_with_name[1] + self.img_ext, merged.height, merged.width)
        if self.debug:
            print(self.prettify(xml_tree))
        xml = ElementTree.tostring(xml_tree, 'utf8', 'xml')
        xml_tree.clear()
        myfile = open(str(self.dest_folder) + "/" + self.strip_path(Path(page_with_name[1])) + ".xml", "wb")
        myfile.write(xml)
        myfile.close()
        semaphore.release()

    def match_files(self):
        # remove
        print("match_files()")

        """Pairs image with gt-Text and saves it in pairing"""
        for img in self.imgList:
            pairing = []
            img_name = self.strip_path(Path(img.split('.')[0]))
            self.gtList = [f for f in glob.glob(str(self.gt_folder) + "/" + img_name + ".gt.txt")]
            # print("Gt-List: " + str(self.gtList))
            if len(self.gtList) > 0:
                self.nameList.append(img_name)
                pairing.append(img)
                gt_filename = self.gtList[0]
                pairing.append(gt_filename)
                pairing.append(self.get_text(gt_filename))

                if self.pred:
                    pred_filelist = [f for f in glob.glob(str(self.gt_folder) + "/" + img_name + ".pred.text")]
                    if len(pred_filelist) > 0:
                        pred_filename = pred_filelist[0]
                        pairing.append(pred_filename)
                        pairing.append(self.get_text(pred_filename))
                    else:
                        print(
                            f"WARNING: The File {str(self.gt_folder)} {img_name}.pred.txt could not be found! "
                            f"Omitting line from page")
                self.matches.append(pairing.copy())
            else:
                print(
                    f"WARNING: The File {str(self.gt_folder)} {img_name}.gt.txt could not be found! Omitting line "
                    f"from page")
        # remove
        # print("New Name_list - " + str(self.nameList))
        # print("Pairing: " + str(pairing))
        # print("Matches: " + str(self.matches))

    def merge_images(self, page):
        # remove
        # print("merge_images(" + str(page) + ")")
        """Merge list of images into one, displayed on top of each other
        :return: the merged Image object
        """
        img_list = []
        img_width = 0
        img_height = 0
        spacer_height = self.spacer * (len(page) - 1)
        for line in page:
            image_data = Image.open(line[0])
            # print("line: " + str(line))
            # print("Image Data: " + str(image_data)) #remove
            image = image_data.copy()
            image_data.close()
            (width, height) = image.size
            img_width = max(img_width, width)
            img_height += height
            img_list.append(image)
        if 'nrm' not in self.img_ext:
            result = Image.new('RGB', (img_width + self.border * 2, img_height + self.border * 2 + spacer_height),
                               (255, 255, 255))
        else:
            result = Image.new('LA', (img_width + self.border, img_height + self.border + spacer_height))
        before = self.border

        for img in img_list:
            result.paste(img, (self.border, before))
            before += img.size[1] + self.spacer
            img.close()
        return result

    def build_xml(self, line_list, img_name, img_height, img_width):
        # remove
        # print("build_xml(" + str(line_list) + ", " + str(img_name) + ", " + str(img_height) + ", " + str(img_width) + ")")

        """Builds PageXML from list of images, with txt files corresponding to each one of them
        :return: the built PageXml[.xml] file
        """
        pcgts = Element('PcGts')
        pcgts.set('xmlns', 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2017-07-15')
        pcgts.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        pcgts.set('xsi:schemaLocation', self.xmlSchemaLocation)

        metadata = SubElement(pcgts, 'Metadata')
        creator = SubElement(metadata, 'Creator')
        creator.text = self.creator
        created = SubElement(metadata, 'Created')
        generated_on = datetime.now().isoformat()
        created.text = generated_on
        last_change = SubElement(metadata, 'LastChange')
        last_change.text = generated_on

        page = SubElement(pcgts, 'Page')
        page.set('imageFilename', img_name)
        page.set('imageHeight', str(img_height))
        page.set('imageWidth', str(img_width))

        text_region = SubElement(page, 'TextRegion')
        text_region.set('id', 'r0')
        text_region.set('type', 'paragraph')
        region_coords = SubElement(text_region, 'Coords')
        s = str(self.border)
        coord_string = s + ',' + s + ' ' + s + "," + str(img_height - self.border) \
                       + ' ' + str(img_width - self.border) + ',' + str(img_height - self.border) \
                       + ' ' + str(img_width - self.border) + ',' + s
        region_coords.set('points', coord_string)
        i = 1
        last_bottom = self.border
        for line in line_list:
            text_line = SubElement(text_region, 'TextLine')
            text_line.set('id', 'r0_l' + str(self.strip_path(Path(line[0])).split('.')[0].zfill(3)))
            i += 1
            line_coords = SubElement(text_line, 'Coords')
            image = Image.open(line[0])
            (width, height) = image.size
            image.close()
            line_coords.set('points', self.make_coord_string(last_bottom, width, height))
            last_bottom += (height + self.spacer)
            line_gt_text = SubElement(text_line, 'TextEquiv')
            line_gt_text.set('index', str(0))
            unicode_gt = SubElement(line_gt_text, 'Unicode')
            unicode_gt.text = line[2]
            if self.pred:
                line_prediction_text = SubElement(text_line, 'TextEquiv')
                line_prediction_text.set('index', str(1))
                unicode_prediction = SubElement(line_prediction_text, 'Unicode')
                unicode_prediction.text = line[4]

        return pcgts

    def make_coord_string(self, previous_lower_left, line_width, line_height):
        # remove
        # print("make_coord_string(" + str(previous_lower_left) + ", " + str(line_width) + ", " + str(line_height) + ")")

        b = str(self.border)
        p = str(previous_lower_left)
        w = str(line_width + self.border)
        h = str(line_height + previous_lower_left)
        coord_string = b + ',' + p + ' ' + b + "," + h + ' ' + w + ',' + h + ' ' + w + ',' + p
        return coord_string

    def print_self(self):
        """Prints all info saved in the object"""
        # remove
        print("Object_info:")
        print("Creator " + str(self.creator))
        print("Image_Folder - " + str(self.image_folder))
        print("GT_Folder - " + str(self.gt_folder))
        print("Dest_Folder - " + str(self.dest_folder))
        print("Ext - " + str(self.ext))
        print("pred - " + str(self.pred))
        print("Lines - " + str(self.lines))
        print("Spacing - " + str(self.line_spacing))
        print("Border - " + str(self.border))
        print("Debug - " + str(self.debug))
        print("Threads - " + str(self.threads))

        print("Image_List - " + str(self.imgList))
        print("gt_List - " + str(self.gtList))
        print("Name_list - " + str(self.nameList))
        print("Matches - " + str(self.matches))
        print("Spacer - " + str(self.spacer))
        print("\n")
