import json
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap
import os


class CarouselGenerator:
    def __init__(self, width=1080, height=1920):
        # 9:16 aspect ratio for social media posts
        self.width = width
        self.height = height
        self.margin = 100

        # Default colors
        self.default_bg_color = (255, 255, 255)  # White background
        self.light_text_color = (255, 255, 255)  # White text for dark backgrounds
        self.dark_text_color = (30, 30, 30)  # Dark text for light backgrounds

        # Load fonts
        self.load_fonts()

    def load_fonts(self):
        """Load fonts with fallbacks"""
        try:
            self.title_font = ImageFont.truetype(
                "Clearface\clearface_serial-bolditalic.otf", 72
            )
            self.point_font = ImageFont.truetype(
                "Clearface\clearface_serial-regular.otf", 38
            )
            self.number_font = ImageFont.truetype(
                "Clearface\clearface_serial-regular.otf", 34
            )
        except:
            try:
                self.title_font = ImageFont.truetype(
                    "/System/Library/Fonts/Arial.ttf", 72
                )
                self.point_font = ImageFont.truetype(
                    "/System/Library/Fonts/Arial.ttf", 48
                )
                self.number_font = ImageFont.truetype(
                    "/System/Library/Fonts/Arial.ttf", 44
                )
            except:
                self.title_font = ImageFont.load_default()
                self.point_font = ImageFont.load_default()
                self.number_font = ImageFont.load_default()

    def create_solid_background(self, color):
        """Create solid color background"""
        return Image.new("RGB", (self.width, self.height), color)

    def create_image_background(self, image_path):
        """Create background from image (9:16 aspect ratio)"""
        try:
            bg_img = Image.open(image_path).convert("RGB")

            # Resize to fit 9:16 ratio while maintaining aspect ratio
            img_ratio = bg_img.width / bg_img.height
            target_ratio = self.width / self.height

            if img_ratio > target_ratio:
                # Image is wider, fit by height
                new_height = self.height
                new_width = int(new_height * img_ratio)
                bg_img = bg_img.resize(
                    (new_width, new_height), Image.Resampling.LANCZOS
                )
                # Center crop
                left = (new_width - self.width) // 2
                bg_img = bg_img.crop((left, 0, left + self.width, self.height))
            else:
                # Image is taller, fit by width
                new_width = self.width
                new_height = int(new_width / img_ratio)
                bg_img = bg_img.resize(
                    (new_width, new_height), Image.Resampling.LANCZOS
                )
                # Center crop
                top = (new_height - self.height) // 2
                bg_img = bg_img.crop((0, top, self.width, top + self.height))

            return bg_img

        except Exception as e:
            print(f"Could not load image: {image_path} - {e}")
            print("Using white background instead")
            return self.create_solid_background(self.default_bg_color)

    def get_text_color_for_background(self, background_img):
        """Determine best text color based on background brightness"""
        # Sample center area of background
        center_crop = background_img.crop(
            (
                self.width // 4,
                self.height // 4,
                3 * self.width // 4,
                3 * self.height // 4,
            )
        )

        # Calculate average brightness
        pixels = list(center_crop.getdata())
        avg_brightness = sum(sum(pixel[:3]) for pixel in pixels) / (len(pixels) * 3)

        # Return light text for dark backgrounds, dark text for light backgrounds
        return self.light_text_color if avg_brightness < 128 else self.dark_text_color

    def wrap_text(self, text, font, max_width):
        """Wrap text to fit within max_width"""
        lines = []
        words = text.split()
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = self.get_text_bbox(test_line, font)
            text_width = bbox[2] - bbox[0]

            if text_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)

        if current_line:
            lines.append(" ".join(current_line))

        return lines

    def get_text_bbox(self, text, font):
        """Get text bounding box"""
        img = Image.new("RGB", (1, 1))
        draw = ImageDraw.Draw(img)
        return draw.textbbox((0, 0), text, font=font)

    def get_text_height(self, text, font):
        """Get text height"""
        bbox = self.get_text_bbox(text, font)
        return bbox[3] - bbox[1]

    def create_title_page(self, title, background_config):
        """Create title page"""
        # Create background
        if background_config.get("type") == "image":
            bg_img = self.create_image_background(background_config["path"])
        else:  # solid color (default)
            color = background_config.get("color", self.default_bg_color)
            bg_img = self.create_solid_background(color)

        # Determine text color
        text_color = self.get_text_color_for_background(bg_img)

        draw = ImageDraw.Draw(bg_img)

        # Wrap title text
        max_text_width = self.width - (2 * self.margin)
        title_lines = self.wrap_text(title, self.title_font, max_text_width)

        # Calculate total height of title
        line_height = self.get_text_height("Ay", self.title_font)
        total_title_height = (
            len(title_lines) * line_height + (len(title_lines) - 1) * 20
        )

        # Center title vertically
        start_y = (self.height - total_title_height) // 2

        # Draw title
        current_y = start_y
        for line in title_lines:
            bbox = self.get_text_bbox(line, self.title_font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2

            # Add subtle shadow for better readability if needed
            if background_config.get("type") == "image":
                shadow_color = (
                    (0, 0, 0)
                    if text_color == self.light_text_color
                    else (255, 255, 255)
                )
                draw.text(
                    (x + 2, current_y + 2),
                    line,
                    fill=shadow_color,
                    font=self.title_font,
                )

            # Draw main text
            draw.text((x, current_y), line, fill=text_color, font=self.title_font)
            current_y += line_height + 20

        return bg_img

    def points_fit_on_page(self, points):
        """Check if points fit on a single page"""
        total_height = self.margin  # Top margin
        max_text_width = self.width - (2 * self.margin)

        for point in points:
            number_height = self.get_text_height("1.", self.number_font)
            point_lines = self.wrap_text(point, self.point_font, max_text_width - 80)
            point_height = len(point_lines) * self.get_text_height(
                "Ay", self.point_font
            )
            item_height = max(number_height, point_height)
            total_height += item_height + 50  # 50px spacing between points

        total_height += self.margin
        return total_height <= self.height

    def create_content_pages(self, key_points, background_configs):
        """Create pages with key points"""
        pages = []
        current_points = []
        point_index = 0
        page_index = 0

        while point_index < len(key_points):
            temp_points = current_points.copy()

            while point_index < len(key_points):
                temp_points.append(key_points[point_index])

                if self.points_fit_on_page(temp_points):
                    current_points = temp_points.copy()
                    point_index += 1
                else:
                    temp_points.pop()
                    break

            if current_points:
                # Get background config for this page
                bg_config = background_configs[1]

                page = self.create_points_page(
                    current_points,
                    start_number=point_index - len(current_points) + 1,
                    background_config=bg_config,
                )
                pages.append(page)
                current_points = []
                page_index += 1

        return pages

    def create_points_page(self, points, start_number=1, background_config=None):
        """Create a page with key points"""
        # Create background
        if background_config.get("type") == "image":
            bg_img = self.create_image_background(background_config["path"])
        else:  # solid color
            color = background_config.get("color", self.default_bg_color)
            bg_img = self.create_solid_background(color)

        text_color = self.get_text_color_for_background(bg_img)
        draw = ImageDraw.Draw(bg_img)

        current_y = self.margin
        max_text_width = self.width - (2 * self.margin)

        for i, point in enumerate(points):
            point_number = start_number + i

            # Draw number (no background circle)
            number_text = f"{point_number}"
            number_bbox = self.get_text_bbox(number_text, self.number_font)

            number_color = text_color  # Use same as text color
            number_x = self.margin
            number_y = current_y

            draw.text(
                (number_x, number_y),
                number_text,
                fill=number_color,
                font=self.number_font,
            )

            # Draw point text
            point_lines = self.wrap_text(point, self.point_font, max_text_width - 50)
            point_x = (
                number_x + number_bbox[2] + 20
            )  # Indent for point text after number

            line_height = self.get_text_height("Ay", self.point_font)
            text_start_y = current_y

            for j, line in enumerate(point_lines):
                line_y = text_start_y + (j * line_height)

                # Add shadow for image backgrounds
                if background_config.get("type") == "image":
                    shadow_color = (
                        (0, 0, 0)
                        if text_color == self.light_text_color
                        else (255, 255, 255)
                    )
                    draw.text(
                        (point_x + 1, line_y + 1),
                        line,
                        fill=shadow_color,
                        font=self.point_font,
                    )

                draw.text(
                    (point_x, line_y), line, fill=text_color, font=self.point_font
                )

            # Move to next point position
            current_y += len(point_lines) * line_height + 50

        return bg_img

    def generate_carousel(
        self, data, output_dir="carousel_output", background_configs=None
    ):
        """Generate carousel from JSON file"""
        os.makedirs(output_dir, exist_ok=True)

        # with open(json_file_path, "r", encoding="utf-8") as file:
        #     data = json.load(file)

        title = data.get("title", "Untitled")
        key_points = data.get("notes", [])

        print(f"Generating carousel for: {title}")
        print(f"Total key points: {len(key_points)}")

        # Use default white background if none provided
        if not background_configs:
            background_configs = [
                {
                    "type": "solid",
                    "color": (255, 255, 255),
                },  # White background for all pages
            ]

        pages = []

        # Create title page
        title_bg_config = (
            background_configs[0]
            if background_configs
            else {"type": "solid", "color": (255, 255, 255)}
        )
        title_page = self.create_title_page(title, title_bg_config)
        pages.append(title_page)

        # Create content pages
        content_bg_configs = (
            background_configs if len(background_configs) > 1 else background_configs
        )
        content_pages = self.create_content_pages(key_points, content_bg_configs)
        pages.extend(content_pages)

        # Save pages
        for i, page in enumerate(pages):
            filename = f"page_{i + 1:02d}.png"
            filepath = os.path.join(output_dir, filename)
            page.save(filepath, "PNG", quality=95)
            print(f"Saved: {filename}")

        print("\nCarousel generated successfully!")
        print(f"Total pages: {len(pages)}")
        print(f"Output directory: {output_dir}")

        return pages


# # Example usage functions
# def create_sample_json():
#     """Create a sample JSON file for testing"""

#     with open("sample_data.json", "w", encoding="utf-8") as file:
#         json.dump(json_response, file, indent=2, ensure_ascii=False)

#     print("Sample JSON file created: sample_data.json")


# Example background configurations
def example_solid_colors():
    """Example: Different solid color backgrounds"""
    return [
        {"type": "solid", "color": (45, 52, 54)},  # Dark gray
        {"type": "solid", "color": (45, 52, 54)},  # Medium gray
        {"type": "solid", "color": (99, 110, 114)},
        {"type": "solid", "color": (99, 110, 114)},
        {"type": "solid", "color": (99, 110, 114)},
    ]


def example_with_images():
    """Example: Mix of solid colors and images"""
    return [
        {"type": "image", "path": "background1.jpg"},  # Title page with image
        {"type": "solid", "color": (255, 255, 255)},  # White
        {"type": "image", "path": "background2.jpg"},  # Another image
        {"type": "solid", "color": (240, 240, 240)},  # Light gray
    ]


if __name__ == "__main__":
    # Create sample JSON
    # create_sample_json()

    # Example 1: Default white background
    # print("=== Generating with white background ===")

    # generator.generate_carousel("sample_data.json")

    # Example 2: Custom solid colors
    print("\n=== Generating with custom colors ===")
    generator = CarouselGenerator()
    colors_config = example_solid_colors()
    generator.generate_carousel(
        "sample_data.json",
        output_dir="carousel_colors",
        background_configs=colors_config,
    )

    # Example 3: With background images (uncomment if you have images)
    # print("\n=== Generating with background images ===")
    # images_config = example_with_images()
    # generator.generate_carousel('sample_data.json',
    #                           output_dir="carousel_images",
    #                           background_configs=images_config)
