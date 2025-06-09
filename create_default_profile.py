from PIL import Image, ImageDraw
import os

def create_default_profile():
    # Create a 200x200 image with a light gray background
    size = 200
    image = Image.new('RGB', (size, size), '#E0E0E0')
    draw = ImageDraw.Draw(image)
    
    # Draw a circle for the head
    head_radius = size * 0.4
    head_center = (size/2, size/2 - size*0.05)
    draw.ellipse(
        (
            head_center[0] - head_radius,
            head_center[1] - head_radius,
            head_center[0] + head_radius,
            head_center[1] + head_radius
        ),
        fill='#BDBDBD'
    )
    
    # Draw a body
    body_top = head_center[1] + head_radius
    body_bottom = size * 0.9
    body_width = size * 0.6
    draw.rectangle(
        (
            size/2 - body_width/2,
            body_top,
            size/2 + body_width/2,
            body_bottom
        ),
        fill='#BDBDBD'
    )
    
    # Ensure the directory exists
    os.makedirs('src/assets/images', exist_ok=True)
    
    # Save the image
    image.save('src/assets/images/default_profile.png')
    print("Default profile image created successfully!")

if __name__ == '__main__':
    create_default_profile() 