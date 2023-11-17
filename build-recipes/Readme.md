### Create .ico

```
#!/bin/bash
# sudo apt-get install icoutils
for size in 16 32 48 128 256; do
    inkscape -z -o $size.png -w $size -h $size ../docs/artwork/mpldc_icon.svg >/dev/null 2>/dev/null
done
icotool -c -o MPLDataCast.ico 16.png 32.png 48.png 128.png 256.png
rm 16.png 32.png 48.png 128.png 256.png

```


### Create .icns

```
#!/bin/bash
# sudo apt-get install icnsutils
for size in 16 32 48 128 256; do
    inkscape -z -o icon_${size}px.png -w $size -h $size ../docs/artwork/mpldc_icon.svg >/dev/null 2>/dev/null
done
png2icns MPLDataCast.icns icon_*px.png
rm icon_16px.png icon_32px.png icon_48px.png icon_128px.png icon_256px.png

```
