poetry run pyinstaller \
--onefile \
--collect-data snap_arch ./snap_arch/main.py \
--name snap-arch \
--distpath build/snap-arch
