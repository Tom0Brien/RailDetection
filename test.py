import torch
import torchvision.transforms as transforms
from PIL import Image
from train import RailNet

# Load the trained model
model = RailNet()
model.load_state_dict(torch.load('model.pth'))
model.eval()

# Load the image to test
image_path = 'data/A_RP-A-1_ - Scanner 1_SIDE_A - 190307_230736_Scanner_1 - originalpoints/A_RP-A-1_ - Scanner 1_SIDE_A - 190307_230736_Scanner_1 - originalpoints_4_3/A_RP-A-1_ - Scanner 1_SIDE_A - 190307_230736_Scanner_1 - originalpoints_4_3_image.png'
input_image = Image.open(image_path).convert('L')  # convert to grayscale
input_tensor = transforms.ToTensor()(input_image).unsqueeze(0)

# Predict the mask for the input image
with torch.no_grad():
    output = model(input_tensor)

# Threshold the output mask to get binary mask
threshold = torch.nn.Threshold(0.5, 0)
binary_output = threshold(output)

# Save the predicted mask
output_mask = binary_output.squeeze().numpy().astype('uint8') * 255
output_mask = Image.fromarray(output_mask)
output_mask.save('predicted_mask.png')
