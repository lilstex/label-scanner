// Upload Image
const video = document.getElementById('video');
const image = document.getElementById('image');
const captureButton = document.getElementById('captureButton');

navigator.mediaDevices.getUserMedia({ video: true }).then(function(stream) {
  video.srcObject = stream;
  video.play();
});

captureButton.addEventListener('click', function() {
  const canvas = document.createElement('canvas');
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  image.value = canvas.toDataURL('image/jpeg');
});