import streamlit as st
from PIL import Image
import io
import base64
import os
import tempfile
import random
import string


# Encoding function
def encode_image(image_path, sentence, output_image_name):
    img = Image.open(image_path)

    access_code = generate_access_code(10)

    st.text(f"Generated Access Code: {access_code}")

    # Convert the sentence to binary and add the access code
    data = access_code + sentence

    data = ''.join(format(ord(char), '08b') for char in data)

    if len(data) > img.width * img.height * 3:
        return "Data is too large to fit in the image"

    data += "1111111111111110"

    data_index = 0

    for y in range(img.height):
        for x in range(img.width):
            pixel = list(img.getpixel((x, y)))
            for color_channel in range(3):
                if data_index < len(data):
                    data_bits = list(format(pixel[color_channel], '08b'))
                    data_bits[-1] = data[data_index]
                    pixel[color_channel] = int("".join(data_bits), 2)
                    data_index += 1
                img.putpixel((x, y), tuple(pixel))

    with open(output_image_name, "wb") as encoded_image:
        img.save(encoded_image, format="PNG")


# Decoding function
def extract_data_from_image(image_path):
    img = Image.open(image_path)
    data = ""
    access_code = ""

    delimiter = "1111111111111110"
    delimiter_length = len(delimiter)

    data_bits = []
    access_code_bits = []

    for y in range(img.height):
        for x in range(img.width):
            pixel = list(img.getpixel((x, y)))
            for color_channel in range(3):
                data_bits.append(format(pixel[color_channel], '08b')[-1])

                if len(access_code_bits) < 80:
                    access_code_bits.append(format(pixel[color_channel], '08b')[-1])

                if len(data_bits) >= delimiter_length and "".join(data_bits[-delimiter_length:]) == delimiter:
                    data_bits = data_bits[:-delimiter_length]
                    access_code = "".join(access_code_bits)
                    data = "".join(data_bits)
                    return access_code + data

    return access_code + data


def binary_to_ascii(binary_string):
    ascii_characters = [binary_string[i:i+8] for i in range(0, len(binary_string), 8)]
    ascii_text = ''.join([chr(int(char, 2)) for char in ascii_characters])
    return ascii_text


def generate_access_code(length):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length)).upper()


# Create a temporary directory for image storage
tmp_dir = tempfile.TemporaryDirectory()

st.title("Steganography App")

# Define state variables to control the app flow
page = st.selectbox("Select an option", ["Home", "Encode", "Decode"])
upload_image = None  # To store the uploaded image

if page == "Home":
    st.markdown("Please select an option from the dropdown menu.")

elif page == "Encode":
    st.subheader("Encode an Image")

    uploaded_image = st.file_uploader("Upload an image for encoding", type=["jpg", "jpeg", "png"])

    if uploaded_image:
        data = st.text_area("Enter the data you want to encode", max_chars=200)

        if st.button("Encode", key="encoding_button"):
            output_image_name = os.path.join(tmp_dir.name, "encoded_image.png")
            encode_image(uploaded_image, data, output_image_name)

            # Provide the download link for the encoded image
            st.markdown(
                f"**Encoded Image** - [Download](data:file/png;base64,{base64.b64encode(open(output_image_name, 'rb').read()).decode()})")

elif page == "Decode":
    st.subheader("Decode an Image")

    uploaded_image = st.file_uploader("Upload an image for decoding", type=["jpg", "jpeg", "png"])

    if uploaded_image:
        access_code = st.text_input("Enter the access code", max_chars=10).upper()

        if st.button("Decode", key="decoding_button"):
            access_code_and_data = extract_data_from_image(uploaded_image)

            if access_code_and_data:
                user_access_code = access_code
                extracted_access_code_and_data = access_code_and_data

                # Convert the entire extracted binary value to ASCII
                extracted_data = binary_to_ascii(extracted_access_code_and_data)

                # Check the first 10 characters with the user input access code
                if user_access_code == extracted_data[:10]:
                    st.success("Access code is correct.")
                    st.text("Extracted Data:")
                    st.write(extracted_data[20:])  # Display the rest of the data
                else:
                    st.error("Access code does not match.")
            else:
                st.error("No access code or data found in the image.")
tmp_dir.cleanup()