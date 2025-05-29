public class Bird
{
    private int kind;
    public int GetSpeed()
    {
        return ComputeSpeed();
    }

    private int ComputeSpeed()
    {
        switch (kind)
        {
            case 0:
                return 10;
            default:
                throw new ArgumentOutOfRangeException();
        }
    }
}