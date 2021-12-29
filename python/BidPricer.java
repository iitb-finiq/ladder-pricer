// java class that takes fix and a request and gives back the corresponding best price for the requested size
package BidPricer;

import java.util.*;

public class BidPricer{
    private String fix;  // raw fix
    private int maxQuote; // the maximum requested amount till now.
    private ArrayList<Double> dp; // array to store all the prices. dp[i] denotes the best price for i million size
    private Double[] finalDenoms; // available sizes
    private Double[] finalPrices; // corresponding prices

    // parse the fix and get finalDenoms and finalPrices
    public void parseFix(String f) {
        fix = f;
        String[] fixAr = fix.split("\u0001");
        List<Double> denomList = new ArrayList<Double>();
        List<Double> priceList = new ArrayList<Double>();

        // iterate over fix and get the denoms and prices
        for(int i=1;i<fixAr.length;i++) {
            fixAr[i] = fixAr[i].replaceAll("[\\p{Cc}\\p{Cf}\\p{Co}\\p{Cn}]","");
            String[] y = fixAr[i].split("=");
            if (y[0].equals("135") && Double.parseDouble(y[1])%1000000 == 0) {
                denomList.add(Double.parseDouble(y[1])/1000000);
                priceList.add(Double.parseDouble(fixAr[i-2].split("=")[1]));
            }
        }
        finalDenoms = denomList.toArray(new Double[1]);
        finalPrices = priceList.toArray(new Double[1]);
        // for(Double i: finalDenoms) System.out.print(i.toString()+" ");
        // System.out.println("");
        // for(Double i: finalPrices) System.out.print(i.toString()+" ");
        // System.out.println("");

        // initialise the prices. They are initialised to the corresponding prices in the fix
        dp = new ArrayList<Double>(finalDenoms.length);
        dp.add(finalPrices[0]);
        dp.add(finalPrices[0]);
        for(int i=1; i < finalDenoms.length; i++) {
            for(double j=finalDenoms[i-1]+1; j <= finalDenoms[i];j++) {
                dp.add(finalPrices[i]);
            }
        }

        maxQuote = 2;
    }

    // get the Best Price for the requested size
    public double getBestPrice(double notional) {
        if(notional < maxQuote) { // if already calculated, return the value only
            return dp.get((int)Math.ceil(notional));
        }
        else {
            int Size = (int)Math.ceil(notional);
            dp.ensureCapacity(Size+1);
            // use dynamic programming to get the best price
            for(int i=maxQuote; i<=Size; i++) {
                if(i >= dp.size()) 
                    dp.add(Double.POSITIVE_INFINITY);
                for(int j=1; j<=finalDenoms[finalDenoms.length-1]; j++) {
                    if (i < j) continue;
                    double val = (dp.get(i-j)*(i-j) + dp.get(j)*j)/i;
                    dp.set(i, Math.min(dp.get(i), val));
                }
            }

            maxQuote = Size;
            return dp.get(Size);
        }
    }

    public static void main(String[] args) {
        
    }
}
