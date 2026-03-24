CXX := g++
CXXFLAGS := -std=c++20 -O2 -Wall -Wextra -Iinclude 
LDFLAGS = -pthread -latomic
TARGET := benchmark
SRC := BenchmarkSecurity.cpp

$(TARGET): $(SRC)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(SRC) $(LDFLAGS)

clean:
	rm -f $(TARGET)

all:
	./benchmark --queue=ms --ops=10000 --threads=16 \
	&& ./benchmark --queue=lprq --ops=10000 --threads=16 \
	&& ./benchmark --queue=fc --ops=10000 --threads=16


plot:
	python3 plot.py