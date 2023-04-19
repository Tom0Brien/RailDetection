import torch.nn as nn
import os
import torch
import torchvision
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
from glob import glob
from scandir import scandir
import numpy as np

# 1. Custom dataset class


class RailDataset(Dataset):
    def __init__(self, root_dir, transform=None):
        self.root_dir = root_dir
        self.transform = transform

        self.image_files = sorted(
            glob(os.path.join(root_dir, "*/*/*_image.png")))
        self.mask_files = sorted(
            glob(os.path.join(root_dir, "*/*/*_segmentation.png")))

        if len(self.image_files) != len(self.mask_files):
            print
            raise ValueError(
                "Number of image files and mask files do not match.")

    def __len__(self):
        return len(self.image_files)

    def get_file_paths(self):
        image_files = []
        mask_files = []

        for entry in scandir(self.data_root):
            if entry.is_dir():
                for subentry in scandir(entry.path):
                    if subentry.is_dir():
                        image_files.extend(
                            glob(os.path.join(subentry.path, '*.png')))
                        mask_files.extend(
                            glob(os.path.join(subentry.path, '*_segmented.png')))

        return sorted(image_files), sorted(mask_files)

    def __len__(self):
        return len(self.image_files)

    def __getitem__(self, idx):
        # Load image and mask
        image = Image.open(self.image_files[idx]).convert('L')
        mask = Image.open(self.mask_files[idx]).convert('L')

        # Apply transformations if specified
        if self.transform:
            image = self.transform(image)
            mask = self.transform(mask)

        # Convert mask to binary (0 or 1)
        mask = torch.where(mask > 0, torch.tensor([1.0]), torch.tensor([0.0]))

        return image, mask


# 2. Define the neural network architecture


class RailNet(nn.Module):
    def __init__(self):
        super(RailNet, self).__init__()
        self.conv1 = nn.Conv2d(1, 16, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)
        self.fc1 = nn.Linear(32 * 64 * 64, 128)
        self.fc2 = nn.Linear(128, 1)

    def forward(self, x):
        x = F.relu(self.conv1(x))
        x = F.max_pool2d(x, 2)
        x = F.relu(self.conv2(x))
        x = F.max_pool2d(x, 2)
        x = x.view(-1, 32 * 64 * 64)
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return x


# 3. Set up the training loop
def train(model, train_loader, criterion, optimizer, device):
    model.train()
    running_loss = 0.0
    for inputs, targets in train_loader:
        inputs, targets = inputs.to(device), targets.to(device)

        # Flatten the target mask to a single value per image
        targets = targets.view(targets.size(0), -1).mean(dim=1, keepdim=True)

        # Zero the parameter gradients
        optimizer.zero_grad()

        # Forward + backward + optimize
        outputs = model(inputs)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()

        # Print statistics
        running_loss += loss.item() * inputs.size(0)
    return running_loss / len(train_loader.dataset)


# 4. Set up the main function to run the training


def main():
    # Load data
    train_transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor()])
    data_root = 'data'
    train_dataset = RailDataset(data_root, transform=train_transform)
    train_loader = DataLoader(train_dataset, batch_size=4, shuffle=True)

    # Set up device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Initialize the model, loss, and optimizer
    model = RailNet().to(device)
    criterion = torch.nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)

    # Training settings
    num_epochs = 100

    # Train the model
    for epoch in range(1, num_epochs + 1):
        train_loss = train(model, train_loader, criterion, optimizer, device)
        print(f'Epoch: {epoch}, Loss: {train_loss:.4f}')

    # Save the model
    torch.save(model.state_dict(), 'model.pth')


if __name__ == '__main__':
    main()
