import datetime
import math
import os
import sqlite3
from typing import Optional, List, Tuple

from PIL import Image, ImageOps, ImageDraw, ImageFont
import wmi


def get_kobo_drive_letter() -> Optional[str]:
    """
    Get the drive letter of the Kobo eReader.

    :return: The drive letter of the Kobo eReader, or None if the Kobo eReader is not connected.
    """
    wmi_connection = wmi.WMI()
    for disk in wmi_connection.Win32_LogicalDisk():
        if disk.VolumeName == 'KOBOeReader':
            return disk.DeviceID
    return None


def get_kobo_screen_size(drive_letter: str) -> Tuple[int, int, bool]:
    """
    Get the screen size of the Kobo eReader based on user selection.

    :param drive_letter: The drive letter of the Kobo eReader.
    :return: A tuple containing the width, height, and grayscale flag of the Kobo eReader.
    """
    devices = {
        # Device: (width, height, grayscale)
        "Kobo Clara 2e": (1072, 1448, True),
        "Kobo Clara Color": (1072, 1448, False),
        "Kobo Forma": (1440, 1920, True),
        "Kobo Libra H2O": (1264, 1690, True),
        "Kobo Nia": (758, 1024, True),
        "Kobo Libra 2": (1264, 1680, True),
        "Kobo Libra Color": (1264, 1680, False),
        "Kobo Sage": (1440, 1920, True),
        "Kobo Elipsa 2E": (1404, 1872, True)
    }

    print("Select your Kobo device:")
    for i, device in enumerate(devices.keys(), 1):
        print(f"{i}. {device}")

    choice = int(input("Enter the number corresponding to your device: ")) - 1
    selected_device = list(devices.values())[choice]

    return selected_device


def get_recently_read_book_image_ids(drive_letter: str) -> List[str]:
    """
    :param drive_letter: The drive letter where the KoboReader.sqlite file is located.
    :return: A list of recently read book image IDs.

    This method retrieves the image IDs of recently read books stored in KoboReader.sqlite database. It connects to
    the SQLite database using the drive letter provided, and executes a SELECT * query to fetch the imageID values
    from the 'content' table. Only books with ReadStatus = 2 (indicating they have been read) and DateLastRead
    greater than the start of the current year * are considered as recently read.

    Example usage:
        drive_letter = 'C:'  # Replace with the actual drive letter
        recently_read_books = get_recently_read_book_image_ids(drive_letter)
        for image_id in recently_read_books:
            print(image_id)

    Note: This method requires the 'sqlite3' module to be imported.
    """
    read_books: List[str] = []
    kobo_reader_db: str = os.path.join(drive_letter, '.kobo', 'KoboReader.sqlite')
    with sqlite3.connect('file:' + kobo_reader_db + '?mode=ro', uri=True) as kobo_db_conn:
        cursor = kobo_db_conn.cursor()
        cursor.execute("SELECT imageID "
                       "FROM content "
                       "WHERE ReadStatus = 2 AND DateLastRead > datetime('now', 'start of year')"
                       "ORDER BY DateLastRead DESC;")
        for row in cursor:
            read_books.append(row[0])

    return read_books


def find_image_path(drive_letter: str, image_id: str) -> Optional[str]:
    """

    Find Image Path

    Searches for a specific image file in a given directory and its subfolders.

    :param drive_letter: The drive letter of the Kobo.
    :param image_id: The ID of the image to search for.
    :return: The file path of the found image, or None if not found.

    """
    # Directory to search
    search_dir = os.path.join(drive_letter, ".kobo-images")
    # Initialize variable to store the file path
    file_path = None
    # Walk through directory and its subfolders
    for root, dirs, files in os.walk(search_dir):
        for file in files:
            if file.endswith("N3_FULL.parsed") and file.startswith(image_id):
                file_path = os.path.join(root, file)
                break
        if file_path:
            break

    return file_path


def collect_image_from_id(drive_letter: str, image_id: str):
    """
    Collects an image based on the drive letter and image ID.

    :param drive_letter: The drive letter where the image is located.
    :param image_id: The ID of the image to collect.
    :return: The collected image as an instance of the Image class, or None if the image was not found.
    """
    file_path = find_image_path(drive_letter, image_id)
    if file_path:
        return Image.open(file_path, 'r', ).convert('RGBA')
    return None


def generate_screensaver_template(screen_size: Tuple[int, int]):
    """
    Generate the background for the screensaver. Currently, it just generates a static noise effect.
    :param screen_size: A tuple representing the dimensions of the screensaver image. It should contain two integers,
    width and height, in pixels.
    :return: An Image object representing the generated screensaver template.
    """
    screensaver: Image = Image.effect_noise(screen_size, 8)
    return screensaver.convert('RGBA')


def calculate_font_size(text, image_size, font_name='arial.ttf'):
    # Open a dummy image to calculate font size
    dummy_image = Image.new("RGB", image_size, (255, 255, 255))
    dummy_draw = ImageDraw.Draw(dummy_image)

    # Determine the maximum font size that fits the image
    font_size = 1
    font = ImageFont.truetype(font_name, font_size)
    text_width = dummy_draw.textlength(text, font=font)
    while text_width < image_size[0]:
        font_size += 1
        font = ImageFont.truetype(font_name, font_size)
        text_width = dummy_draw.textlength(text, font=font)

    # Decrease font size until it fits
    font_size -= 1

    return font_size


def add_label(screensaver, coordinates):
    """
    Adds a label to the bottom right corner of the screensaver.
    :param screensaver: The screensaver image to add the label to.
    :param coordinates: The coordinates of the bottom right corner of the screensaver.
    :return: An image with the label added to the bottom right corner.
    """
    label_size = (screensaver.size[0] - coordinates[0], screensaver.size[1] - coordinates[1])
    label = Image.new('RGBA', label_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(label)
    text = f'{datetime.datetime.now().year}'
    font_size = calculate_font_size(text, label_size, 'Inkfree.ttf')
    font = ImageFont.truetype("Inkfree.ttf", font_size)  # Adjust the font as needed
    _, _, text_width, text_height = draw.textbbox((0, 0), text, font=font)
    text_x = (label_size[0] - text_width) // 2
    text_y = (label_size[1] - text_height) // 2
    draw.text((text_x, text_y), text, font=font, fill='#575757')

    screensaver.paste(label, coordinates)
    return screensaver


def add_images_to_screensaver(screensaver_template, cover_images, header_size: int = 0, full_screen: bool = False):
    """
    :param full_screen: If True, some books will be cut off for a full screen. Otherwise, there will be half-empty rows.
    :param screensaver_template: The base template image of the screensaver.
    :param cover_images: A list of cover images to be added to the screensaver.
    :param header_size: The height of the header area of the screensaver. Defaults to 0.
    :return: An image with the cover images added to the screensaver template.
    """
    screensaver: Image = screensaver_template.copy()
    width, height = screensaver.size
    height -= header_size
    total_images = len(cover_images)
    # Calculate the number of columns and rows
    columns = math.ceil(math.sqrt(total_images))
    rows = math.ceil(total_images / columns)
    if total_images == 2:
        rows += 1
    if full_screen:
        rows = math.floor(total_images / columns)
    # Calculate the width and height of each cell
    cell_width = width // columns
    cell_height = height // rows
    # Calculate the padding between cells
    padding = math.ceil(0.01 * cell_width)
    # Resize the cover images to fit the cells
    cover_images = [img.resize((cell_width, cell_height)) for img in cover_images]
    # Add the cover images to the screensaver
    x = y = 0
    for i, img in enumerate(cover_images):
        x = (i % columns) * (cell_width + padding)
        y = header_size + (i // columns) * (cell_height + padding)
        screensaver.paste(img, (x, y), img)

    if screensaver.size[0] - x > cell_width:
        screensaver = add_label(screensaver, (x + cell_width, y))
    return screensaver


def save_screensaver(screensaver, kobo_drive):
    """
    :param screensaver: The screensaver image to be saved.
    :param kobo_drive: The path to the Kobo device's drive.
    :return: None

    Saves the screensaver image to the specified location on the Kobo device's drive.
    The saved file will have the format '<year>Progress.png', where 'year' is the current year.
    The screensaver image should be in PNG format.
    """
    os.makedirs(os.path.join(kobo_drive, '.kobo', 'screensaver'), exist_ok=True)
    screensaver_path = os.path.join(kobo_drive, '.kobo', 'screensaver', f'{datetime.datetime.now().year}Progress.png')
    screensaver.save(screensaver_path, 'PNG')


def main():
    # Get the drive letter of the Kobo eReader
    kobo_drive: str = get_kobo_drive_letter()
    if not kobo_drive:
        print('Kobo eReader not connected.', flush=True)
        os.system('pause')
        return
    print(f'Kobo eReader found at {kobo_drive}', flush=True)

    # Get the image IDs of recently read books
    read_books: List[str] = get_recently_read_book_image_ids(kobo_drive)
    if not read_books:
        print('No recently read books found.', flush=True)
        os.system('pause')
        return
    print(f'{len(read_books)} recently read books found.', flush=True)

    # Collect the cover images of recently read books
    cover_images: List = [collect_image_from_id(kobo_drive, image_id) for image_id in read_books]
    # Filter out not found images
    cover_images = [img for img in cover_images if img]
    if not cover_images:
        print('No cover images found.', flush=True)
        os.system('pause')
        return
    print(f'{len(cover_images)} cover images found.', flush=True)

    # Get the screen size of the Kobo eReader
    x, y, grayscale = get_kobo_screen_size(kobo_drive)
    screen_size = (x, y)

    if grayscale:
        # Grayscale the images
        print('Grayscaling the images...', flush=True)
        cover_images = [ImageOps.grayscale(img).convert('RGBA') for img in cover_images]

    # Resize the images to fit the screen aspect ratio (keep width, adjust height) for uniform look
    print('Resizing the images...', flush=True)
    cover_images = [img.resize((img.width, img.width * screen_size[1] // screen_size[0])) for img in cover_images]

    # Create screensaver template
    screensaver_template: Image = generate_screensaver_template(screen_size)

    # Add the cover images to the screensaver template add a header size if needed
    print('Adding cover images to the screensaver template...', flush=True)
    screensaver: Image = add_images_to_screensaver(screensaver_template, cover_images, header_size=0)

    # Save the screensaver to the Kobo
    save_screensaver(screensaver, kobo_drive)
    print('Screensaver saved to Kobo.', flush=True)


if __name__ == '__main__':
    main()
