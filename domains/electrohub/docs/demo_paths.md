# Demo Paths

Three scripted paths for the ElectroHub electronics retail demo. Each one is
designed to show the difference between structured tool use and generic RAG.

> Tip: Run each opening question once in Context Retriever mode and then repeat
> it in Simple RAG mode to show how the tool-enabled system reaches live
> product, store, and order data.

## Path 1: Product Fit to Local Pickup

1. Ask: "I am looking for a MacMini to run OpenClaw on, what machines do you have in stock that would help?"
   Expected outcome: the agent recommends 2-3 computer products instead of TVs or accessories. The strongest fits are usually `ByteForge Micro Pro`, `NovaBook 14 Creator`, and `PulseTower Mini RTX 4060`, with concrete hardware and price details.
2. Follow with: "And can I pick that up at my local store?"
   Expected outcome: the agent uses the signed-in profile, identifies `ElectroHub Cherry Creek` as the home store, and confirms same-day pickup for the recommended products that are in local inventory.
3. Follow with: "Which one is the best value?"
   Expected outcome: the agent compares price, form factor, and headroom, typically positioning `ByteForge Micro Pro` as the best compact value and `PulseTower Mini RTX 4060` as the stronger performance step-up.

RAG contrast: Simple RAG can talk generally about buying a PC for retro games, but it cannot know what is actually in stock or what Maya's local store is.

## Path 2: Shipment Delay Investigation

1. Ask: "I haven't received my shipment yet."
   Expected outcome: the agent finds `ORD_EH_1001`, reports the original promise date, current tracking number, latest scan at the Salt Lake City facility, and the weather-delay reason.
2. Follow with: "When should I expect it now?"
   Expected outcome: the agent cites the updated estimated delivery from `SHIP_EH_001` and distinguishes it from the missed original promise date.
3. Follow with: "Has support already opened a case?"
   Expected outcome: the agent surfaces `CASE_EH_001` and explains that the shipment-delay case is already open.

RAG contrast: Simple RAG can explain shipping delays in general terms, but it cannot identify Maya's order, tracking number, current location, or active case.

## Path 3: Store-Aware Commerce Memory

1. Ask: "Show me my recent ElectroHub orders."
   Expected outcome: the agent summarizes the signed-in customer's recent shipping and pickup orders, including order totals and fulfillment types.
2. Follow with: "Which one did I pick up locally?"
   Expected outcome: the agent identifies `ORD_EH_1002` and names `ElectroHub Cherry Creek`.
3. Follow with: "Do you offer curbside there?"
   Expected outcome: the agent confirms curbside support at that store using the store record.

RAG contrast: Simple RAG can describe a generic pickup policy, but it has no access to Maya's order history or her preferred store.
