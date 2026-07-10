# Compliance Blocklist

> This file is both human-readable policy documentation and machine-parsed rule data.
> Format: Each rule starts with `## Rule N:` heading. Key-value pairs use `**Key**: value` syntax.
> The ComplianceChecker parses these fields: `Categories`, `Subcategories`, `Keywords`, `Platforms`, `Action`.
> Multi-value fields use comma-separated lists. Matching is case-insensitive substring on `category` and `subcategory`,
> and case-insensitive containment on `normalized_keywords`.
>
> Policy sources: Meta Advertising Standards (facebook.com/policies/ads), TikTok Advertising Policies
> (ads.tiktok.com/help/article/ad-policies). Rules represent genuinely known restricted/prohibited categories
> on these platforms as of mid-2026.

---

## Rule 1: Dietary Supplements & Weight Loss Claims

**Categories**: dietary supplements, weight loss supplements, herbal supplements, nutritional supplements, sports supplements, meal replacements, superfood powders, detox supplements, colon cleanse, appetite suppressants, fat burners, pre-workout supplements, post-workout supplements, nootropic supplements, cognitive enhancers

**Subcategories**: diet pills, weight loss pills, fat burner pills, appetite suppressant pills, detox tea, cleansing tea, slimming tea, keto pills, carb blockers, metabolism boosters, muscle builders, testosterone boosters, HGH supplements, DHEA supplements, melatonin supplements, sleep aids, adaptogens, ashwagandha supplements, CBD supplements

**Keywords**: weight loss, fat burner, lose weight, burn fat, appetite suppressant, detox cleanse, colon cleanse, slimming, rapid weight loss, extreme weight loss, before and after, weight loss results, keto diet, ketosis, fat burning, metabolism boost, diet pills, tummy tuck, body detox, cleanse diet, skinny, slim down, shed pounds, miracle weight loss

**Platforms**: meta, tiktok

**Action**: block

**Geo Notes**: US allows many OTC supplements with disclaimers; EU Novel Foods Regulation restricts herbal/botanical supplements not approved prior to 1997; Canada restricts weight-loss and detox claims under the Food and Drugs Act; Australia's TGA regulates supplements as therapeutic goods in some cases. Russia and Japan have additional pre-approval requirements. Geo-specific matching is not implemented yet — see Sprint 1.2.2 for the LLM gray-area check and Sprint 3.x for full geo-awareness.

---

## Rule 2: Weapons, Firearms & Weapons-Adjacent Items

**Categories**: weapons, firearms, guns, ammunition, knives, bladed weapons, tactical gear, self-defense tools, hunting equipment, airsoft guns, paintball guns, bb guns, crossbows, archery equipment, throwing stars, brass knuckles, batons, stun guns, tasers, pepper spray, mace

**Subcategories**: pistol accessories, rifle accessories, gun holsters, ammunition boxes, gun safes, knife sets, tactical knives, hunting knives, pocket knives, sword replicas, martial arts weapons, concealed carry, gun parts, firearm scopes, gun cleaning kits

**Keywords**: tactical knife, hunting knife, pocket knife, switchblade, butterfly knife, throwing knife, combat knife, survival knife, boot knife, neck knife, gun holster, concealed carry holster, firearm, pistol, rifle, shotgun, semi-automatic, assault rifle, handgun, revolver, ammunition, bullet, magazine clip, gun parts, AR-15, AK-47, gun accessory, weapon accessory, body armor, ballistic vest, bulletproof, tactical vest, pepper spray, stun gun, taser, brass knuckles, throwing stars, nunchucks, butterfly knife trainer

**Platforms**: meta, tiktok

**Action**: block

**Geo Notes**: Meta generally prohibits firearms, ammunition, and weapon accessories globally with few exceptions. TikTok's policy is similar — no weapons, ammunition, or weapon accessories. Knife restrictions vary: many countries allow pocket knives under a certain blade length (e.g., UK limits folding knives to 3 inches, Germany allows 12cm fixed blades for sporting use). Pepper spray is legal in the US but restricted in the UK, EU, Canada, and Australia. Geo-specific matching is not implemented yet.

---

## Rule 3: Adult Content & Sexual Wellness

**Categories**: adult content, adult entertainment, sexual wellness, sex toys, adult toys, intimate products, lingerie, erotic apparel, dating services, escort services, adult media, pornography, XXX, explicit content, fetish products, bondage equipment, sex education, marital aids

**Subcategories**: vibrators, dildos, lubricants, adult DVDs, adult subscriptions, webcam services, adult dating apps, hookup apps, phone sex, erotic literature, nude art, strip clubs, pole dancing equipment, adult novelties, edible underwear, body paint, massage oils, condoms, pregnancy tests

**Keywords**: sex toy, adult toy, vibrator, dildo, lubricant, lube, bondage, BDSM, fetish, adult video, explicit content, XXX, porn, nude, naked, erotic, sex shop, adult entertainment, webcam, cam girl, escort, dating app, hookup, sex chat, phone sex, sensual massage, erotic massage, strip club, pole dance, onlyfans, fansly, adult content creator, NSFW, sexual wellness

**Platforms**: meta, tiktok

**Action**: block

**Geo Notes**: Meta prohibits adult products and services globally. Sex education content is generally allowed but not sexually suggestive advertising. TikTok similarly prohibits adult content with very limited exceptions. Condoms and pregnancy tests are generally allowed on Meta (not adult products) — this rule focuses on the genuinely restricted categories. Some countries (e.g., Middle Eastern nations) have broader restrictions — geo-specific matching is not implemented yet.

---

## Rule 4: Counterfeit, Replica & IP-Infringing Goods

**Categories**: counterfeit goods, replica products, fake products, knockoffs, imitation brands, designer replicas, luxury replicas, counterfeit electronics, counterfeit apparel, counterfeit accessories, unlicensed merchandise, bootleg products, pirated content, copyright-infringing goods, trademark-infringing goods, patent-infringing goods

**Subcategories**: fake handbags, fake watches, replica sneakers, replica shoes, replica clothing, replica jewelry, replica sunglasses, replica belts, counterfeit credit card, fake IDs, bootleg movies, bootleg music, unlicensed sports merchandise, unlicensed character merchandise, replica jerseys, fake beauty products, counterfeit cosmetics, fake perfumes, counterfeit phone accessories, counterfeit charging cables, counterfeit headphones, fake tech products

**Keywords**: replica, counterfeit, fake, knockoff, imitation, dupe, inspired by, lookalike, AAA quality, mirror quality, 1:1, perfect copy, exact copy, high quality replica, luxury replica, designer replica, replica handbag, replica watch, replica shoes, replica sneakers, replica clothing, replica jewelry, fake rolex, fake gucci, fake louis vuitton, fake nike, fake airpods, fake iphone, fake apple, unbranded designer, no logo, brand quality without the price tag, inspired by designer, similar to gucci, hermes style, prada style, copyright free, unlicensed, bootleg, pirate

**Platforms**: meta, tiktok

**Action**: block

**Geo Notes**: Both platforms strictly prohibit counterfeit goods globally. China and Southeast Asia are major source regions for counterfeit goods — sellers from these regions face elevated scrutiny. The EU has particularly strong trademark enforcement under EUIPO. Some "inspired by" or "dupe" content (where the product is not claiming to be the original brand) exists in a gray area — the LLM gray-area check (Sprint 1.2.2) will handle borderline cases. Meta's IP infringement reporting is governed by the Meta Brand Rights tool; TikTok's by their Intellectual Property Policy.

---

## Rule 5: Tobacco, Vaping & Recreational Drugs

**Categories**: tobacco products, cigarettes, cigars, smokeless tobacco, chewing tobacco, snus, vaping products, e-cigarettes, vape pens, vape juice, e-liquid, nicotine products, nicotine pouches, herbal cigarettes, hookahs, shisha, recreational drugs, cannabis, marijuana, THC products, CBD products, hemp products, kratom, kava, peyote, salvia, psychedelics, magic mushrooms, LSD, ecstasy, cocaine, heroin, methamphetamine, poppers, nitrous oxide

**Subcategories**: vape mods, vape tanks, vape coils, vape batteries, disposable vapes, pod systems, nicotine salts, vape juice flavors, delta-8 THC, delta-9 THC, THCa, THC gummies, THC vape, CBD flower, CBD isolate, full spectrum CBD, broad spectrum CBD, cannabis flower, marijuana edibles, cannabis concentrates, cannabis tinctures, cannabis topicals, cannabis seeds, grow lights, hydroponic equipment, bongs, pipes, rolling papers, grinders, dugouts, one hitters, dab rigs, vaporizers, dry herb vaporizers, wax pens, drug paraphernalia, kratom powder, kratom capsules, kava root, kava powder

**Keywords**: vape, e-cigarette, e-cig, vape pen, vape juice, e-liquid, nicotine, nicotine salt, disposable vape, vape mod, vape tank, vape coil, vape battery, puff bar, elf bar, geek bar, lost mary, vaping, smoke shop, head shop, bong, pipe, water pipe, dab rig, wax pen, one hitter, dugout, rolling paper, grinder, dry herb vaporizer, cannabis, marijuana, weed, THC, CBD, delta-8, delta-9, hemp flower, cannabis flower, marijuana edible, THC gummy, THC edible, cannabis tincture, kratom, kava, psychedelic, magic mushroom, psilocybin, LSD, acid, ecstasy, molly, cocaine, crack, heroin, meth, crystal meth, amphetamine, prescription stimulant, opioid, fentanyl, oxycodone, hydrocodone, xanax, valium, adderall, ritalin, benzodiazepine

**Platforms**: meta, tiktok

**Action**: block

**Geo Notes**: Tobacco and vaping products face broad restrictions globally. Meta prohibits the sale of tobacco and vaping products. TikTok similarly prohibits. Cannabis advertising is illegal under US federal law despite state-level legalization — both Meta and TikTok follow federal law. CBD policy continues to evolve: Meta allows topical CBD (non-ingestible) in some regions with pre-approval. The EU classifies many CBD products as Novel Foods requiring authorization. UK allows CBD as a food supplement with specific conditions. Australia requires prescription for CBD. Kratom is legal at US federal level but banned in several states (Alabama, Arkansas, Indiana, Rhode Island, Vermont, Wisconsin) and in many other countries (UK, EU, Australia, Malaysia, Thailand, Japan). Geo-specific matching is not implemented yet.

---

## Rule 6: Prescription & Pharmaceutical Products

**Categories**: prescription drugs, prescription medications, pharmaceutical products, controlled substances, narcotics, sedatives, stimulants, antidepressants, antipsychotics, blood pressure medications, diabetes medications, cholesterol medications, pain relievers, antibiotics, antivirals, antifungals, chemotherapy drugs, hormone therapy, birth control, fertility drugs, erectile dysfunction drugs, hair loss treatments, acne treatments, rosacea treatments, psoriasis treatments, eczema treatments

**Subcategories**: online pharmacy, mail order pharmacy, prescription delivery, prescription discount card, generic viagra, generic cialis, generic levitra, generic propecia, generic ozempic, generic wegovy, generic mounjaro, generic semaglutide, generic tirzepatide, weight loss injections, GLP-1 agonists, semaglutide, tirzepatide, compounded semaglutide, research chemicals, peptide therapy, SARMs, selective androgen receptor modulators, MK-677, RAD-140, ostarine, cardarine, ibutamoren, liothyronine, clenbuterol, anavar, winstrol, anadrol, trenbolone, equipoise, primobolan, deca-durabolin

**Keywords**: prescription, medication, pharmaceutical, pharmacy online, buy meds online, online pharmacy, no prescription needed, without prescription, prescription free, buy prescription drugs, cheap medication, generic drugs, generic viagra, generic cialis, erectile dysfunction, ED pills, hair loss treatment, propecia, finasteride, minoxidil, acne treatment, accutane, isotretinoin, weight loss injection, ozempic, wegovy, mounjaro, semaglutide, tirzepatide, saxenda, liraglutide, GLP-1, peptide, SARMs, research chemical, steroid, anabolic steroid, testosterone replacement, HRT, hormone replacement, anti-aging, HGH, human growth hormone, IGF-1, clenbuterol, phentermine, adipex, contrave, qsymia, orlistat, alli, xenical, belviq, diethylpropion, phendimetrazine, benzphetamine, methamphetamine prescription

**Platforms**: meta, tiktok

**Action**: block

**Geo Notes**: Online pharmacies that sell prescription drugs without a valid prescription are prohibited globally. Meta allows certified online pharmacies in some countries (e.g., US VIPPS-certified pharmacies) with specific authorization. GLP-1 weight loss drugs (Ozempic, Wegovy, Mounjaro) are a rapidly evolving regulatory area — generic/compounded versions and telemedicine prescribing have created gray areas. SARMs and research chemicals are unapproved drugs in most markets and prohibited by both platforms. Anabolic steroids are controlled substances in the US (Schedule III) and prohibited by both platforms. EU member states have individual regulations on prescription drug advertising, generally more restrictive than US. Geo-specific matching is not implemented yet.

---

## Rule 7: Alcohol & Alcoholic Beverages

**Categories**: alcoholic beverages, beer, wine, spirits, liquor, whiskey, vodka, rum, gin, tequila, brandy, cognac, liqueur, cider, hard seltzer, alcopops, premixed cocktails, sake, vermouth, fortified wine

**Subcategories**: craft beer, microbrew, wine club, wine subscription, liquor delivery, alcohol delivery, beer delivery, spirit samples, alcohol samples, home brewing kits, brewing supplies, distilling equipment, moonshine still, wine making kit, beer making kit, alcohol brewing, distilling

**Keywords**: alcohol, beer, wine, spirits, liquor, whiskey, vodka, rum, gin, tequila, brandy, cognac, bourbon, scotch, liqueur, alcoholic, drunk, drinking game, beer pong, happy hour, wine tasting, liquor store, alcohol delivery, beer delivery, wine delivery, home brewing, distilling, moonshine, brewery, distillery, winery, drink responsibly

**Platforms**: meta, tiktok

**Action**: block

**Geo Notes**: Alcohol advertising is restricted, not universally prohibited, on both platforms. Meta allows alcohol ads with age and country targeting restrictions (minimum 18+ in most countries, 21+ in US). TikTok allows alcohol ads in some regions with age restrictions. Since geo-aware targeting is not implemented yet, the deterministic checker blocks all alcohol as a conservative default. The LLM gray-area check (Sprint 1.2.2) can handle cases where geo-specific targeting might make an alcohol ad permissible. Some countries (e.g., Saudi Arabia, Kuwait, Iran) prohibit alcohol advertising entirely. Russia restricts alcohol advertising heavily.

---

## Rule 8: Gambling & Casino-Related Products

**Categories**: gambling, casino, betting, sports betting, poker, online casino, slot machines, roulette, blackjack, baccarat, craps, bingo, lottery, scratch cards, raffle, sweepstakes, daily fantasy sports, esports betting, horse racing betting, dog racing, mahjong, card games for money

**Subcategories**: casino chips, poker chips, poker table, poker set, roulette wheel, blackjack table, slot machine, slot machine parts, lottery tickets, scratch off, betting tips, gambling strategy, betting system, gambling system, casino equipment, gaming chips, dealer equipment, card counters, bookmaking

**Keywords**: casino, gambling, bet, betting, sports bet, sportsbook, poker online, online casino, slot machine, roulette, blackjack, baccarat, craps, lottery, scratch card, scratch off, raffle, sweepstakes, daily fantasy, DFS, fantasy sports, esports betting, horse bet, horse racing, parlay, accumulator, over under, point spread, moneyline, gambling strategy, betting tip, poker tournament, texas holdem, blackjack strategy, card counting, beat the casino, jackpot, progressive jackpot, vegas, las vegas, slot, bet now, sign up bonus, deposit bonus, free bet, risk free bet, first deposit, welcome offer, no deposit bonus, betting odds, odds comparison

**Platforms**: meta, tiktok

**Action**: block

**Geo Notes**: Gambling advertising is heavily regulated. Meta requires written permission (licensing) for gambling ads in most allowed jurisdictions. TikTok has a limited list of countries where gambling ads are permitted (primarily UK, Ireland, and a few others). Most countries restrict gambling ads to age-verified audiences. The US varies by state — legal in NJ, PA, MI, WV, CT, AZ, VA, CO, IL, IN, IA, TN, WY, KS, AR, NY, MD, LA, MA, OH, NE, ME, but blocked or limited in others. This deterministic rule blocks all gambling as a conservative default; the LLM gray-area check can handle permissible cases with proper geo targeting.

---

## Clear-Pass Reference Cases

The following categories are NOT flagged by any rule above. They are documented here as known-clear reference cases for testing and auditing purposes.

**Category**: Kitchen Tools & Accessories
**Subcategories**: cookware, bakeware, utensils, knives, cutting boards, measuring cups, mixing bowls, kitchen gadgets, food storage containers, kitchen scales, thermometers, peelers, graters, colanders, strainers, whisks, spatulas, tongs, ladles, rolling pins, pastry brushes, cookie cutters, icing tools, piping bags, pastry tips, dough scrapers, bench scrapers, kitchen shears, pizza cutters, vegetable choppers, mandoline slicers, spiralizers, garlic presses, herb choppers, salad spinners, vegetable peelers, zesters, citrus juicers, can openers, bottle openers, corkscrews, measuring spoons, kitchen timers, oven mitts, pot holders, aprons, dish towels, placemats, trivets, coasters
**Keywords**: kitchen tools, kitchen gadgets, cooking utensils, bakeware, cookware set, non-stick pan, cast iron skillet, chef's knife, paring knife, bread knife, cutting board, measuring cups, mixing bowls, kitchen scale, food thermometer, oven mitt, apron, dish towel, kitchen shears, pizza cutter, vegetable peeler

**Platforms**: meta, tiktok

**Action**: allow

---

**Category**: Pet Accessories & Supplies
**Subcategories**: dog beds, cat beds, pet collars, pet leashes, pet harnesses, pet bowls, pet feeders, pet toys, pet grooming tools, cat trees, scratching posts, pet carriers, pet travel accessories, pet waste bags, litter boxes, litter scoops, pet food storage, pet water fountains, pet clothing, pet life jackets, pet tags, identification tags, pet first aid kits
**Keywords**: pet accessories, dog bed, cat bed, pet bed, dog collar, cat collar, pet leash, dog leash, pet harness, dog harness, pet bowl, pet feeder, pet toys, dog toy, cat toy, pet grooming, brush, comb, nail clipper, pet shampoo, cat tree, scratching post, pet carrier, dog carrier, waste bags, poo bags, litter box, cat litter, pet food storage, water fountain, pet fountain, pet tag, ID tag

**Platforms**: meta, tiktok

**Action**: allow

---

## Rule Schema

Each rule above follows this structure:
- A `## Rule N:` heading (N = number) or a `## Category:` heading (for clear-pass references)
- `**Categories**:` — comma-separated category name patterns (matched via case-insensitive substring on `ProductIdentity.category`)
- `**Subcategories**:` — comma-separated subcategory name patterns (matched via case-insensitive substring on `ProductIdentity.subcategory`)
- `**Keywords**:` — comma-separated keyword patterns (matched via case-insensitive containment check on `ProductIdentity.normalized_keywords`)
- `**Platforms**:` — target platforms
- `**Action**:` — `block` (flagged) or `allow` (explicitly cleared)
- Optional: `**Geo Notes**:` — human-readable notes about geo-specific variations

A match on ANY field (Categories, Subcategories, or Keywords) for a rule with `Action: block` will flag the product.
