import streamlit as st
import zipfile
import os
from io import BytesIO
from src.carousel_generator import CarouselGenerator, example_solid_colors
from src.content_generator import content_generator


def generate_content(url: str):
    content = content_generator(url)
    carousel_generator = CarouselGenerator()
    config = example_solid_colors()
    carousel = carousel_generator.generate_carousel(
        data=content, output_dir="carousel_output", background_configs=config
    )

    # Ensure this returns a list of file paths
    if isinstance(carousel, list) and all(isinstance(p, str) for p in carousel):
        return carousel
    else:
        # Try to collect file paths manually from the output dir
        return [
            os.path.join("carousel_output", f)
            for f in os.listdir("carousel_output")
            if f.endswith((".png", ".jpg"))
        ]


def zip_files(file_paths):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for path in file_paths:
            zip_file.write(path, arcname=os.path.basename(path))
    zip_buffer.seek(0)
    return zip_buffer


# Streamlit UI
st.title("🎠 YouTube Carousel Generator")

url = st.text_input("Enter YouTube Video URL")

if st.button("Generate Carousel"):
    if not url:
        st.warning("Please enter a valid YouTube URL.")
    else:
        with st.spinner("Generating carousel..."):
            output_files = generate_content(url)
            if output_files:
                st.success("Carousel generated successfully!")

                zip_data = zip_files(output_files)

                st.download_button(
                    label="📥 Download Carousel (ZIP)",
                    data=zip_data,
                    file_name="carousel.zip",
                    mime="application/zip",
                )
            else:
                st.error("Failed to generate carousel.")
