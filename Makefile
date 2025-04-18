CXX      = clang++
CXXFLAGS = -std=c++17 -O2
OBJDIR   = obj
OBJS     = $(OBJDIR)/marauder_server.o

# default target
mm: $(OBJS)
	$(CXX) $(CXXFLAGS) $(OBJS) -o mm           

# pattern rule: .cpp  →  .o
$(OBJDIR)/%.o: %.cpp
	@mkdir -p $(OBJDIR)                       
	$(CXX) $(CXXFLAGS) -Iinc -c $< -o $@       

.PHONY: clean
clean:
	rm -rf $(OBJDIR) mm