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
	./benchmark --queue=ms --ops=1000 && ./benchmark --queue=lprq --ops=1000 && python3 plot.py

plot:
	python3 plot.py