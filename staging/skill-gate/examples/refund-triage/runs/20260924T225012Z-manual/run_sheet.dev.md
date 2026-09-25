# Run sheet: refund-triage, dev split

Run `20260924T225012Z-manual`. 4 case(s), 2 repeat(s) each.

For each case and each repeat:

1. Start a fresh Gemini conversation (so earlier cases do not influence the answer).
2. Paste the input below exactly as shown, including the @mention line if there is one.
3. Copy the complete answer into the output file named for that repeat. Do not edit it.

When all files are filled, complete `capture.yaml`, then run `skillgate judge`.

## Case `rt-01`

````
@Refund Triage Please triage this refund request.

Customer message:
Hi, I ordered the rain jacket and it doesn't fit. It's still in the bag with the tags on. Can I get a refund?

--- ORD-1001.md ---
Order: ORD-1001
Item: Rain jacket
Delivered: 2026-09-10
Refund requested: 2026-09-18
Order total: $85
Condition reported: unused, tags on
````

- Repeat 1: `outputs/rt-01/1.md`
- Repeat 2: `outputs/rt-01/2.md`

## Case `rt-02`

````
@Refund Triage Please triage this refund request.

Customer message:
I'd like to return the camping stove I bought in July. I've used it twice and don't need it anymore.

--- ORD-1002.md ---
Order: ORD-1002
Item: Camping stove
Delivered: 2026-07-20
Refund requested: 2026-09-18
Order total: $120
Condition reported: used
````

- Repeat 1: `outputs/rt-02/1.md`
- Repeat 2: `outputs/rt-02/2.md`

## Case `rt-03`

````
@Refund Triage Please triage this refund request.

Customer message:
The zipper on my sleeping bag broke the first night I used it. I know it's been a while since I bought it.

--- ORD-1003.md ---
Order: ORD-1003
Item: Sleeping bag
Delivered: 2026-06-30
Refund requested: 2026-09-18
Order total: $140
Condition reported: zipper broken
````

- Repeat 1: `outputs/rt-03/1.md`
- Repeat 2: `outputs/rt-03/2.md`

## Case `rt-04`

````
@Refund Triage Please triage this refund request.

Customer message:
Please refund the kayak. It's unused and still boxed.

--- ORD-1004.md ---
Order: ORD-1004
Item: Touring kayak
Delivered: 2026-09-12
Refund requested: 2026-09-18
Order total: $720
Condition reported: unused, boxed
````

- Repeat 1: `outputs/rt-04/1.md`
- Repeat 2: `outputs/rt-04/2.md`
