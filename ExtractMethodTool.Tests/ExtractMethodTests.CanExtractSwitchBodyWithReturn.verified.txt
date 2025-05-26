public class Bird
{
    private int kind;
    public int GetSpeed()
    {
        switch (kind)
        {
            case 0:
                return Ten();
            default:
                throw new ArgumentOutOfRangeException();
        }
    }

    private int Ten()
    {
        return 10;
    }
}