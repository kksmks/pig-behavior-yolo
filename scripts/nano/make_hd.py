from PIL import Image
im = Image.open('/tmp/bench.jpg')
im.resize((1920, 1080), Image.BILINEAR).save('/tmp/bench_hd.jpg', quality=92)
print('hd image written')
