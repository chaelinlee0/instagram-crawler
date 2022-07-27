def text_analysis():
    results_str = " ".join(results)
    tokens = results_str.split(" ")
    text = nltk.Text(tokens)
    topWord = text.vocab().most_common(i)
    target = 30
    xlist = [a[0] for a in topWord[:i]]
    ylist = [a[1] for a in topWord[:i]]

    plt.figure(figsize=(10, 5))  # 그래프 크기 지정
    plt.xlabel('Word')  # X축 이름
    plt.xticks(rotation=70)  # X축 라벨 회전
    plt.ylabel('Count')  # Y축 이름
    plt.title('keyword TOP ' + str(i) + ' WORD')
    plt.ylim([0, i])  # 그래프의 Y축 크기 조절
    plt.bar(xlist, ylist)  # bar로 실행하면 막대그래프. plot으로 실행하면 꺾은선 그래프.

if __name__ == "__main__":
    text_analysis()
