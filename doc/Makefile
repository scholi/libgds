LOGS=aux toc toc.old log bbl blg snm
TEX=latex-mk
DVIPS=dvips
PSTOPDF=ps2pdf

all: gds.pdf

%.pdf: %.ps
	$(PSTOPDF) $<

%.ps: %.dvi
	$(DVIPS) $<

%.dvi: %.tex
	$(TEX) $<

clean:
	@(rm -f $(patsubst %,gds.%,$(LOGS)))

mrproper: clean
	@(rm -f $(patsubst %,gds.%,dvi ps pdf))
