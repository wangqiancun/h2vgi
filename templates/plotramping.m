clc
clear
M = xlsread('netload+FCEV(V1G).xlsx');
colors=distinguishable_colors(6)

plot(M(:,12)/1000000,'color',colors(1,:),'linewidth',1);
hold on 
plot(M(:,13)/1000000,'color',colors(2,:),'linewidth',1);
hold on 
plot(M(:,14)/1000000,'color',colors(3,:),'linewidth',1);
hold on 
plot(M(:,15)/1000000,'color',colors(4,:),'linewidth',1);
hold on 
plot(M(:,16)/1000000,'color',colors(5,:),'linewidth',1);
hold on 
plot(M(:,17)/1000000,'color',colors(6,:),'linewidth',1);

xlabel('Time','FontName','Times New Roman','FontSize',20)
ylabel('Net Load(GW)','FontName','Times New Roman','FontSize',20)
set(gca,'FontName','Times New Roman','FontSize',20)
set(gca, 'XTick', [0:24*2:288])
set(gca,'XTickLabel',{'0:00', '4:00', '8:00', '12:00', '16:00', '20:00', '24:00'})
legend('Capacity Factor=1','Capacity Factor=0.9','Capacity Factor=0.8','Capacity Factor=0.7','Capacity Factor=0.6','Netload')
%legend('Electrolyzer Capacity =100%','Electrolyzer Capacity =125%','Electrolyzer Capacity =165%')

grid on