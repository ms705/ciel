package skywriting.examples.grep;

public class IncrementerCombiner implements Combiner<IntWritable> {
	
	public IntWritable combine(IntWritable oldValue, IntWritable increment) {
		IntWritable newValue = new IntWritable();
		
		newValue.set(oldValue.get() + increment.get());
		
		return newValue;
	}

	@Override
	public IntWritable combineInit(IntWritable initVal) {
		
		return initVal;
		
	}
	
}
