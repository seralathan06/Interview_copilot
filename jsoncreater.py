import json
import re

# Assuming your current questions_data is loaded as a list containing one large dict
# For this example, let's re-create it from your paste:
current_malformed_data = [
  {
    "id": 1,
    "question": "Accenture Aptitude Questions and Answers with Explanation 1. A certain number of men take 45 days to complete work. If there are 10 men less then they will take 60 days to complete the work. Find the original number of men. A. 50 B. 60 C. 30 D. 40 Answer – D. 40 Explanation: Let us assume initially there are X men. Then x*45 = (x-10)*60. So we get x = 40 2. 5 men and 10 boys can do a piece of work in 30 days and 8 men and 12 boys can do the work in 20 days then the ratio of daily work done by a man to that of a boy. A. 5:1 B. 4:5 C. 6:1 D. 7:3 Answer – C. 6:1 Explanation: Given that, 5m + 10b = 1/30 and 8m + 12b = 1/20 after solving we get m = 1/200 and b = 1/1200 so required ratio = (1/200) : (1/1200) = 6:1 3. 4 women and 5 men working together can do 3 times the work done by 2 women and one man together. Calculate the work of a man to that of a woman. A. 1:1 B. 3:2 C. 1:2 D. 2:1 Answer – A. 1:1 Explanation: Given 4w + 5m = 3*(2w + m) i.e. 2w = 2m so the ratio of work done by man to woman is 1:1 Accenture Aptitude Questions and Answers with Explanation 4. Manoj can do a work in 20 days, while Chandu can do the same work in 25 days. They started the work jointly. A few days later Suresh also joined them and thus all of them completed the whole work in 10 days. All of them were paid total Rs.1000. What is the share of Suresh? A. 100 B. 300 C. 200 D. 400 Answer – A. 100 Explanation: Efficiency of Manoj = 5% The efficiency of Chandu = 4% They will complete only 90% of the work = [(5+4)*10] =90 Remaining work was done by Suresh = 10%. Share of Suresh = 10/100 * 1000 = 100 5. Nagarjuna lends Rs 30,000 of two of his friends. He gives Rs 15,000 to the first at 6% p.a. simple interest. He wants to make a profit of 10% on the whole. The simple interest rate at which he should lend the remaining sum of money to the second friend is A. 8% B. 12% C. 14% D. 16% Answer - C. 14% Explanation: Simple Interest on Rs 15000 =(15000\u00d76\u00d71)/100 = Rs. 900 Profit to made on Rs 30000 = 30000\u00d710/100=Rs 3000 Simple Interest on Rs.15000 = 3000-900 = Rs.2100 Rate=(S.I.* 100)/(P * T)=(2100\u00d7100)/15000 =14% per annum Therefore, the simple interest rate at which he should lend the remaining sum of money to the second friend is 14% Accenture Aptitude Questions and Answers with Explanation 6. A portion of $6600 is invested at a 5% annual return, while the remainder is invested at a 3% annual return. If the annual income from the portion earning a 5% return is twice that of the other portion, what is the total income from the two investments after one year? A. 270 B. 250 C. 280 D. 200 Answer - A. 270 Explanation: According to the given data 5x + 3y = z (total) x + y = 6600 5x= 2(3y) [ condition given] 5x \u2013 6y = 0 x + y = 6600 5x -6y = 0 Subtract both equations and you get x = 3600 so y = 3000 3600*.05 = 180 3000*.03 = 90 z (total) = 270 Therefore, the total income from the two investments after one year = 270 7. While calculating the weight of a group of men, the weight of 63 kg of one of the member was mistakenly written as 83 kg. Due to this the average of the weights increased by half kg. What is the number of men in the group? A. 25 B. 20 C. 40 D. 60 Answer - C. 40 Explanation: Increase in marks lead to an increase in average by 1/2 So (83-63) = x/2 x = 40 Therefore, the number of men in the group are 40 Accenture Aptitude Questions and Answers with Explanation 8. In a group of 8 boys, 2 men aged at 21 and 23 were replaced, two new boys. Due to this the average cost of the group increased by 2 years. What is the average age of the 2 new boys? A. 17 B. 30 C. 28 D. 23 Answer - B. 30 Explanation: According to the given data Average of 8 boys increased by 2, this means the total age of boys increased by 8*2 = 16 yrs So sum of ages of two new boys = 21+23+16 = 60 Average of these = 60/2 = 30 9. A Boat takes total 16 hours for traveling downstream from point A to point B and coming back point C which is somewhere between A and B. If the speed of the Boat in Still water is 9 Km/hr and the rate of stream is 6 Km/hr, then what is the distance between A and C? A. 60 Km B. 90 Km C. 30 Km D. Cannot be determined Answer – D. Cannot be determined Explanation: 16 = D/9+6 + x/9-6 10. A Boat going upstream takes 8 hours 24 minutes to cover a certain distance, while it takes 5 hours to cover 5/7 of the same distance running downstream. Then what is the ratio of the speed of boat to speed of water current? A. 11:5 B. 11:6 C. 11:1 D. 6:5 Accenture Aptitude Questions and Answers with Explanation Answer – C. 11:1 Explanation: (S-R)*42/5 = (S+R)*7 S:R = 11:1 11. A Boat takes 128 min less to travel to 48 Km downstream than to travel the same distance upstream. If the speed of the stream is 3 Km/hr. Then Speed of Boat in still water is? A. 12 Km/hr B. 15 Km/hr C. 6 Km/hr D. 9 Km/hr Answer – A. 12 Km/hr Explanation: 32/15 = 48(1/s-3 – 1/s+3) s= 12 Therefore, Speed of Boat in still water is 12 Km/hr. 12. An alloy contains Brass, Iron, and Zinc in the ratio 2:3:1 and another contains Iron, zinc, and lead in the ratio 5:4:3. If equal weights of both alloys are melted together to form a third alloy, then what will be the weight of lead per kg in new alloy? A. 1/4 B. 41/7 C. 1/8 D. 51/9 Answer – C. 1/8 Explanation: Shortcut: In the first alloy, 2:3:1 =6*2 5:4:3 =12 Multiply 2 to make it equal, 4:6:2 5:4:3 Adding all, 4:11:6:3=24 3/24=1/8 Accenture Aptitude Questions and Answers with Explanation 13. A milkman mixes 6 liters of free tap water with 20litres of pure milk. If the cost of pure milk is Rs.28 per liter the % Profit of the milkman when he sells all the mixture at the cost price is A. 30% B. 16(1/3)% C. 25% D. 16.5% Answer – A. 30% Explanation: Profit=28*6=728 Cp=28*20=560 Profit = 168*100/560=30% 14. 144 liters of the mixture contains milk and water in the ratio 5: 7. How much milk needs to be added to this mixture so that the new ratio is 23: 21 respectively? A. 40 liters B. 28 liters C. 32 liters D. 36 liters Answer – C. 32 liters Explanation: 144 == 5:7 60: 84 Now == 21 = 84 23 = 92 92-60 = 32 15. A shopkeeper bought 30kg of rice at Rs.75 per kg and 20 kg of rice the rate of Rs.70. per kg.If he mixed the two brand of rice and sold the mixture at Rs.80 per kg. Find his gain A. Rs.350 B. Rs.550 C. Rs.420 D.Rs.210 Answer – A. Rs.350 Accenture Aptitude Questions and Answers with Explanation Explanation: CP = 30*75 + 20*70 = 2250 + 1400 = 3650 SP =80*(30+20) = 4000 Hence, Gain = 4000-3650 = 350 16. Cost price of 80 notebooks is equal to the selling price of 65 notebooks. The gain or loss % is A. 32% B. 42% C. 27% D. 23% Answer – D. 23% Explanation: % = [80 – 65/65]*100 = 15*100/65 = 1500/65 = 23.07 = 23% profit Therefore, the gain percentage is 23%. 17. Eight years ago, Pranathi’s age was equal to the sum of the present ages of her one son and one daughter. Five years hence, the respective ratio between the ages of her daughter and her son that time will be 7:6. If Pranathi’s husband is 7 years elder to her and his present age is three times the present age of their son, what is the present age of the daughter? A. 19 years B. 27 years C. 15 years D. 23 years Answer – D. 23 years Explanation: P – 8 = S + D —(1) 6D + 30 = 7S + 35 —(2) H = 7 + P H = 3S 3S = 7 + P —-(3) Solving equation (1),(2) and (3) D = 23 Therefore, the present age of the daughter is 23 years Accenture Aptitude Questions and Answers with Explanation 18. Shas married 8 year ago. Today her age is 9/7 times to that time of marriage. At present his son’s age is 1/6th of her age. What was her son’s age 3 year ago? A. 4 yr B. 2 yr C. 3 yr D. 5 yr Answer – B. 2 yr Explanation: Let us assume that Sravan’s age 8 year ago = x Present age = x + 8 x + 8 = 9/7 x 7(x + 8)= 9x x = 28; 28 + 8 = 36 Son’s age = 1/6 * 36 = 6 Son’s age 4 year ago = 6-4 =2 19. The respective ratio between the present age of Mani and Dheeraj is x : 42. Mani is 8 years younger than Murali. Murali’s age after 8 years will be 33 years. The difference between Dheeraj’s and Mani’s age is same as the present age of Murali. What is the value of x? A. 18 B. 10 C. 16 D. 17 Answer – D. 17 Explanation: Murali’s age after 8 years = 33 years Murali’s present age = 33 – 8= 25 years Mani’s present age = 25 – 8 = 17 years Dheeraj’s present age = 17 + 25 = 42 years Ratio between Mani and Dheeraj = 17: 42 X = 17 20. Revanth’s present age is three times his son’s present age and 4/5th of his father’s present age. The average of the present ages of all of them is 62 years. What is the difference between the Revanth’s son’s present age and Revanth’s father’s present age? Accenture Aptitude Questions and Answers with Explanation A. 64 years B. 69 years C. 66 years D. 62 years Answer – C. 66 years Explanation: Present age of Revanth is = 4/5x Present age of Revanth’s father is = 4/15x Ratio = 15: 12 : 4 Difference between the Revanth’s son’s present age and Revanth’s father’s present age = 62/31 * 3(15 – 4). = 2*3*11 = 66 years. 21. 36% of 945 – 26% of 765 + 17.7 =? A. 167 B. 187 C. 159 D. 143 Answer – C. 159 Explanation: 340.2 – 198.9 =141.3+17.7 = 159 22. √(456÷12+142-11) =? A. 11 B. 169 C. 23 D. 13 Answer – D. 13 Explanation: 38+142-11 = 169 = 13*13 23. 1(1/5) of 1(1/2) of ? = 216 A. 100 B. 125 C. 140 D. 120 Accenture Aptitude Questions and Answers with Explanation Answer – D. 120 Explanation: 6/5*3/2 *x = 216 X = 216*2*5/6*3 = 2160/18 = 120 24. 15 32 60 122 240 ? A. 488 B. 482 C. 364 D. 362 Answer – B. 482 Explanation: 15 * 2 + 2 = 32 32 * 2 – 4 = 60 60 * 2 + 2 = 122; 122 * 2 – 4 = 240 Then 240*2 + 2 = 482 25. 18 10 8 9 11.5 ? A. 10.75 B. 18.75 C. 19.75 D. 14.75 Answer – D. 14.75 Explanation: 18 / 2 + 1 = 10 10 / 2 + 3 = 8 8 / 2 + 5 = 9 9 / 2 + 7 = 11.5 11.5 / 2 + 9 = 14.75"
  }
]

fixed_questions = []
# The main content is in the 'explanation' field of the first (and only) item
# This is a very fragile way to parse, assuming specific patterns.
# A more robust solution would involve a custom parser or proper structured input.
full_text = current_malformed_data[0]['question']

# Regex to split based on question numbers
# This regex is simplified and might need adjustments based on actual content variations
# It tries to split by " [Number]. "
raw_questions = re.split(r'\s*\d+\.\s*', full_text)

# Remove the first element if it's empty or an intro text
if "Accenture Aptitude Questions and Answers with Explanation" in raw_questions[0]:
    raw_questions = raw_questions[1:]

question_id_counter = 1
for q_text in raw_questions:
    if not q_text.strip():
        continue

    # Try to extract question, options, answer, and explanation
    question_match = re.match(r'^(.*?)\s*(A\.\s*.*?)\s*(B\.\s*.*?)\s*(C\.\s*.*?)\s*(D\.\s*.*?)\s*Answer\s*[\u2013-]\s*([A-D])\.\s*(.*?)\s*Explanation:\s*(.*)$', q_text, re.DOTALL | re.IGNORECASE)
    
    if question_match:
        question_content = question_match.group(1).strip()
        options = [
            question_match.group(2).strip(),
            question_match.group(3).strip(),
            question_match.group(4).strip(),
            question_match.group(5).strip()
        ]
        correct_answer_letter = question_match.group(6).upper()
        explanation_content = question_match.group(8).strip()

        option_letters = ['A', 'B', 'C', 'D']
        correct_option_index = -1
        if correct_answer_letter in option_letters:
            correct_option_index = option_letters.index(correct_answer_letter)

        fixed_questions.append({
            "id": question_id_counter,
            "question": question_content,
            "options": options,
            "correct_option_index": correct_option_index,
            "explanation": explanation_content
        })
        question_id_counter += 1
    else:
        print(f"Could not parse: {q_text[:100]}...") # Debugging unparsed sections

# Save the new structure
with open("D:\\GEN AI\\APITUDE_ASSIATANT\\ApitiAssistant\\data\\questions.json", "w", encoding="utf-8") as f:
    json.dump(fixed_questions, f, indent=2, ensure_ascii=False)

print("Fixed questions saved to questions_fixed.json")