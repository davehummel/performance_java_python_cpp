package technology.workhorse.benchmarks;

import java.io.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Consumer;
import java.util.function.Function;
import java.util.stream.Collectors;
import java.util.stream.IntStream;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;

/**
 * @author David Hummel - dmhummel@gmail.com
 *
 * Submission Notes: These additional considerations in scale, performance and application were applied:
 * <p>
 * Symbol Expansion: It is assumed that over time the supported symbols may grow (beyond 'A'-'Z').  The MIN_SYMBOL and
 * MAX_SYMBOL class constants may be changed to expand the usable range.  With thousands of symbols, tree depth may
 * lead to function recursion that trigger stack overflows. This implementation avoids unbounded function recursion
 * <p>
 * Streaming and Concurrency: This support continuous concurrent streams of input, as is common in real world use-cases.
 * The solution class is broken into two public functions: consumeText(Reader) and getSnapshot()
 * In the test cases, one is called after the other.  However, one or more consumeText() can be invoked on separate
 * threads, and run continuously. The function will run until the reader source is closed, blocking when data is not yet
 * available. At any time, getSnapshot() may be called and will generate the S-Expression for the current known tree.
 * Validation for errors E1,E2 are checked in consumeText(), E3-E5 in getSnapshot()
 * <p>
 * Memory: The solution was designed to minimize memory footprint by progressively processing input from the Reader.
 * Only the accumulated of nodes as a Binary Tree and a lookup array of pointers to nodes. Both are bounded to the size
 * of the symbol set (26 in this case).
 *
 * <p>
 * Performance: Overall performance is limited by the wait/block cycle for listening to the console input.
 * For potential application to larger problems, this implementation supports parallel stream processing.
 * An array based node lookup table is used due to its performance advantage. For example, with ~20k symbols:
 * Total:0.029274 Consume:0.017369 Snapshot:0.011905 - array
 * Total:0.040492 Consume:0.025022 Snapshot:0.015470 - map
 * <p>
 * Parallel streams are disabled as the example using symbols A-Z are too small to benefit.
 * <p>
 * Errors: "If errors are present, print out the first listed error below"
 * This was interpreted to apply for the entire input set, not a specific input edge pair.
 * This means the solution waits until all pairs are processed before throwing E3,E4,E5
 */

public class Solution {

    /**
     * Entry point for test
     *
     * @param args Not used
     * @throws Exception
     */
    public static void main(String args[]) throws Exception {
        /* Enter your code here. Read input from STDIN. Print output to STDOUT */

        BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
//        BufferedReader reader = new BufferedReader(testRandomValid(  -1, new Random(2))); // Set seed here to repeat random outcomes

        long startTime = System.nanoTime();
        long consumeTime = 0;
        InputException exception = null;
        String output = null;
        Solution tree = new Solution();
        try {
            tree.consumeText(reader);
            consumeTime = System.nanoTime() - startTime;
            output = tree.getSnapshot();
        } catch (InputException e) {
            exception = e;
        } finally {
            long endTime = System.nanoTime() - startTime;
            System.err.printf("Total:%.6f Consume:%.6f Snapshot:%.6f%n", endTime / 1e9, consumeTime / 1e9, (endTime - consumeTime) / 1e9);
        }
        if (exception != null) {
            System.out.println("E" + exception.id);
        } else {
            System.out.println(output);
        }
    }


    // try MAX_SYMBOL = 20000 with 'testRandomValid()' input above for a large problem example.
    public static final char MIN_SYMBOL = 'A', MAX_SYMBOL = 'Z' /*20000*/;
    private static final int INPUT_BLOCK_SIZE = "(X,Y) ".length();

    // This is the aggregation container that new input is fed into.  Even at 20000, an array out-performs a hashmap
    private final LinkedNode nodeArray[] = new LinkedNode[MAX_SYMBOL - MIN_SYMBOL + 1];

    // State held to ensure an E3 was never thrown before an E2
    private boolean tooManyChildState = false;


    /**
     * Processes and validates input text, updating the state of the tree.
     * This can be called more than once and concurrently.
     * Validation will occur for exception states E1 and E2.
     *
     * @param reader Reader source of characters
     * @throws InputException type E1 and E2
     */
    public void consumeText(Reader reader) throws InputException {
        Stream<String> edgeSourceStream = edgeStringStream(reader); // blocking stream based on Reader for input
        edgeSourceStream.map(this.extractPairsFunction()).forEach(this.addPairsFunction());

    }

    /**
     * Generates S-Expression as String the current tree and verifies E3,E4,E5 error states
     * This function may be called multiple times and concurrently with itself and consumeText()
     *
     * @return a String S-Expression Representation
     */
    public String getSnapshot() {
        // Delayed throwing this to ensure all E2 errors can be thrown
        if (tooManyChildState)
            throw new InputException(3);

        // This reference can be safely used from a lambda, even with parallel stream execution
        AtomicReference<LinkedNode> root = new AtomicReference<>();

        synchronized (Solution.this) { // shares syncrhonization with
            long nodeCount = streamNodes().peek(node -> {
                if (!node.hasParent()) {
                    LinkedNode oldRoot = root.getAndSet(node);
                    if (oldRoot != null)
                        throw new InputException(4);
                }
                node.setExplored(false);
            }).count();

            if (root.get() == null)
                throw new InputException(5);

            StringBuilder sb = new StringBuilder();

            int foundCount = explore(root.get(), sb);

            // If there is only one root, but not all nodes are found
            // there must be a disconnected cycle
            if (foundCount < nodeCount)
                throw new InputException(5);

            return sb.toString();
        }
    }


    /**
     * Returns a mapping function for both validating input stream of Strings and extracting the edge pairs into Character[2]
     * This is coded to expect 6 character with spaces at the end, or a 5 character block for the end of the stream.
     * Any other input will trigger an E1 error.
     *
     * @return Mapping Function to from String to Character[2] stream
     */
    private Function<String, Character[]> extractPairsFunction() {
        return text -> {
            if (text.length() == INPUT_BLOCK_SIZE) { //Verify space separator
                if (text.charAt(INPUT_BLOCK_SIZE - 1) != ' ') throw new InputException(1);
            } else if (text.length() != INPUT_BLOCK_SIZE - 1) { // Last block should only be length 5
                throw new InputException(1);
            }
            // verify content
            if (text.charAt(0) != '(' || text.charAt(2) != ',' || text.charAt(4) != ')')
                throw new InputException(1);

            // verify symbols
            char c1 = text.charAt(1);
            char c2 = text.charAt(3);
            if (c1 < MIN_SYMBOL || c1 > MAX_SYMBOL || c2 < MIN_SYMBOL || c2 > MAX_SYMBOL)
                throw new InputException(1);

            return new Character[]{c1, c2};
        };
    }

    /**
     * Returns a consumer function that adds nodes and edges to the tree within the Solution class.
     * This function is protected with a synchronized block to allow for concurrent insertions and to pause input
     * when a snapshot is generating.
     *
     * @return Consumer for Charcter[2] edge pairs
     */
    private Consumer<Character[]> addPairsFunction() {
        return c -> {
            synchronized (Solution.this) {
                LinkedNode root = getOrCreateNode(c[0]);
                LinkedNode child = getOrCreateNode(c[1]);

                // Delayed throwing this to ensure all E2 errors can be thrown
                if (root.addChild(child) == 3)
                    tooManyChildState = true;
            }
        };
    }


    /**
     * Returns a known node for this id or generates, stores and returns a new node.
     * This should be called within a synchronized block.
     *
     * @param id node id
     * @return LinkedNode
     */
    private LinkedNode getOrCreateNode(char id) {
        int index = id - MIN_SYMBOL;
        if (nodeArray[index] == null) {
            nodeArray[index] = new LinkedNode(id);
        }
        return nodeArray[index];

    }

    /**
     * Returns a stream of all known nodes.
     * Should only be called within a synchronized block coordinated with callers of getOrCreateNode
     *
     * @return Stream of all LinkedNodes
     */
    private Stream<LinkedNode> streamNodes() {
        return Arrays.stream(nodeArray).filter(node -> node != null);
    }


    /**
     * Node class that manages parent -> child unidirectional relationships
     * <p>
     * Note:
     * - Validation for duplicate nodes is done in the addChild function.
     * - Identify for hash and comparison is based only on the value of the node and ignores child edges.
     */
    private class LinkedNode {

        private final char value;
        private LinkedNode lesserChild = null, greaterChild = null;

        private boolean hasParent;
        private boolean explored;

        /**
         * Constructs a node with no children
         *
         * @param value char value to be set for this node
         */
        public LinkedNode(char value) {
            this.value = value;
        }

        /**
         * The addChild function attempts to add a new child to this node.
         * It will detect duplicate pairs and throw an E2.
         * When adding a second child that is less than the first, the values are swapped to ensure ordering
         *
         * @param child LinkedNode to add as child
         * @return number of children (3 in the case of an overloaded node)
         */
        public int addChild(LinkedNode child) throws InputException {

            child.setHasParent();
            if (lesserChild == null) {
                lesserChild = child;
                return 1;
            } else if (greaterChild == null) {
                int compare = lesserChild.value - child.value;
                if (compare == 0) { //
                    throw new InputException(2);
                } else if (compare < 0) {
                    greaterChild = child;
                } else {
                    greaterChild = lesserChild;
                    lesserChild = child;
                }
                return 2;
            } else {
                // Check for a repeated value, even in a full child scenario
                if (lesserChild.value == child.value || greaterChild.value == child.value) {
                    throw new InputException(2);
                }
                // You could throw an E3 exception right here
                // but the requirements imply future Duplicate Pair exception (E2) to be identified before E3
                return 3;
            }
        }

        /**
         * Called whenever a node is added as a child.
         * This is used for identifying roots later.
         */
        private void setHasParent() {
            this.hasParent = true;
        }

        /**
         * Returns true if this node has had a parent node attached during consumeText()
         *
         * @return true if this node has a parent
         */
        public boolean hasParent() {
            return hasParent;
        }

        /**
         * Sets a nodes explored state, returning its previous value
         *
         * @param newVal value to set explored state
         * @return previous explored state
         */
        public boolean setExplored(boolean newVal) {
            boolean oldValue = explored;
            explored = newVal;
            return oldValue;
        }

    }


    /**
     * Stack managed implementation of DFS for cycle detection and text output
     * Avoided recursion for potential stack overflow risk when applied to larger symbol sets and deeper trees
     *
     * @param start starting node
     * @param sb    StringBuilder for text output
     * @return count of explored nodes
     */
    private int explore(LinkedNode start, StringBuilder sb) throws InputException {
        int count = 0;
        List<LinkedNode> stack = new ArrayList<>();
        List<Integer> branchDepths = new ArrayList<>();
        stack.add(start);
        branchDepths.add(0);
        int depth = 0;
        LinkedNode node;
        while (!stack.isEmpty()) {
            while ((node = stack.remove(0)).lesserChild != null) {
                depth++;
                count++;
                if (node.greaterChild != null) {
                    stack.add(0, node.greaterChild);
                    branchDepths.add(0, depth);
                }
                exploreVisit(node, sb);
                stack.add(0, node.lesserChild);
            }
            depth++;
            count++;
            exploreVisit(node, sb);
            int branchDepth = branchDepths.remove(0);
            for (int i = 0; i < depth - branchDepth; i++)
                sb.append(")");
            depth = branchDepth;
        }
        return count;
    }

    /**
     * Wraps behavior for each visit of a node, including cycle check
     *
     * @param node visited LinkedNode
     * @param sb   accumulating StringBuilder
     * @throws InputException Thrown on loop detection
     */
    private void exploreVisit(LinkedNode node, StringBuilder sb) throws InputException {
        if (node.setExplored(true))
            throw new InputException(5);
        sb.append("(");
        sb.append(node.value);
    }

    /**
     * Constructs a blocking stream based on BufferedReader source.
     * Blocks on input stream, emitting number pairs after parsing either a block of 6 characters or, after
     * the stream closes, the remaining characters.  The limitation of core Java 8 libraries that reliably block on
     * console input made for additional complexity.
     *
     * @param reader
     * @return Stream of Strings
     */
    private Stream<String> edgeStringStream(Reader reader) {
        return StreamSupport.stream(
                Spliterators.spliteratorUnknownSize(
                        new Iterator<String>() {
                            private final char[] buffer = new char[INPUT_BLOCK_SIZE];
                            private String next = null;
                            private boolean initialized = false;
                            private boolean terminated = false;

                            private void loadNextString() {
                                initialized = true;
                                int i = 0;
                                try {
                                    // read() was the only blocking function for reading chars
                                    // that seemed to work in Java 8
                                    while (i < INPUT_BLOCK_SIZE) {
                                        int r = 0;
                                        r = reader.read();
                                        if (r == -1) {
                                            if (i != INPUT_BLOCK_SIZE - 1)
                                                throw new InputException(1);
                                            terminated = true;
                                            break;
                                        }
                                        buffer[i] = (char) r;
                                        i++;
                                    }
                                } catch (IOException e) {
                                    throw new InputException(1);
                                }

                                next = String.copyValueOf(buffer, 0, i);
                            }

                            @Override
                            public boolean hasNext() {
                                if (!initialized)
                                    loadNextString();
                                return (next != null);
                            }

                            @Override
                            public String next() {
                                if (!initialized)
                                    loadNextString();

                                String out = next;
                                if (!terminated)
                                    loadNextString();
                                else
                                    next = null;

                                return out;
                            }
                        },
                        Spliterator.ORDERED)
                , false);
    }

    /**
     * Standard runtime exception for validation failures
     */
    static class InputException extends RuntimeException {
        public final int id;

        InputException(int id) {
            this.id = id;
        }

        @Override
        public String toString() {
            return "E" + id;
        }

    }


    // TEST CODE - Input stream sources used for performance and random input testing

    // Massive input set with no duplicate (but guaranteed to have cycles)
    // for stress testing consume process
    static BufferedReader testHugeRandom(Random randomSource) {
        List<Integer> range1 = randomize(IntStream.rangeClosed(MIN_SYMBOL, MAX_SYMBOL - 1).boxed().collect(Collectors.toList()), randomSource);
        List<Integer> range2 = randomize(IntStream.rangeClosed(MIN_SYMBOL + 1, MAX_SYMBOL).boxed().collect(Collectors.toList()), randomSource);


        StringBuilder builder = new StringBuilder();

        for (int i = 0; i < range1.size() / 2 - 1; i++) {
            List<Integer> range3 = new LinkedList<>(range2);
            for (int x : range1) {
                builder.append("(" + (char) (x) + "," + (char) range3.remove(0).intValue() + ") ");
            }
            range2.add(0, range2.remove(range2.size() - 1));
        }

        builder.deleteCharAt(builder.length() - 1);
        String output = builder.toString();
//        System.out.println(output);
        return new BufferedReader(new StringReader(output));
    }


    // Raandom construction to build a valid tree with no cycles
    static BufferedReader testRandomValid(int edgeCount, Random randomSource) {
        if (edgeCount <= -1 || edgeCount > MAX_SYMBOL - MIN_SYMBOL)
            edgeCount = MAX_SYMBOL - MIN_SYMBOL;
        if (edgeCount < 1) edgeCount = 1;


        List<Integer> range1 = new LinkedList<>();
        range1.add((int) MIN_SYMBOL);
        List<Integer> range2 = randomize(IntStream.rangeClosed(MIN_SYMBOL + 1, MIN_SYMBOL + edgeCount).boxed().collect(Collectors.toList()), randomSource);

        StringBuilder builder = new StringBuilder();


        while (range1.size() > 0) {
            if (range2.size() == 0)
                break;
            int parent = range1.remove(0);
            int addCount = randomSource.nextInt(3);
            if (addCount == 0 && range1.size() == 0) {
                addCount = 1;
            }

            for (int i = 0; i < addCount; i++) {
                if (range2.size() == 0)
                    break;
                int child = range2.remove(0);
                range1.add(child);
                builder.append("(" + (char) (parent) + "," + (char) child + ") ");
            }
        }

        builder.deleteCharAt(builder.length() - 1);
        String output = builder.toString();
        System.out.println(output);
        return new BufferedReader(new StringReader(output));
    }

    /**
     * Test function for shuffling a list
     *
     * @param list List of integers
     * @return randomized Integer list
     */
    static List<Integer> randomize(List<Integer> list, Random randomSource) {
        List<Integer> output = new ArrayList<>();
        while (list.size() > 0) {
            int a = list.remove(randomSource.nextInt(list.size()));
            output.add(a);
        }
        return output;
    }


}


