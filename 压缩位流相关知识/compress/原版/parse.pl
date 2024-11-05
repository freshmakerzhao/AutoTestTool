#!/usr/bin/perl -w
use strict;
use JSON;

my $registerHash = &getConfigReg();
my $MAXNUM = 9999999*101;

open LIST,"parse.list";
while (<LIST>){
    next if(/^\s*$/ or /^\#/);
    chomp;
    s/\r//g;
    s/\s*$//g;
    if(/\.rbt$/){
        &parseRbt($_);
    }elsif(/\.rbd$/){
        &parseRbd($_);
    }elsif(/\.mcs$/){
        &parseMcs($_);
    }elsif(/\.msd$/){
        &parseMsd($_);
    }else{
        print "Sorry, file: $_ is not supported in current version!\n";
    }
}
close LIST;

sub parseMcs{
    my $mcsName = shift;
    open MCS,"$mcsName" or die "cannot open $mcsName";
    open RBT,">$mcsName.rbt" or die "cannot create $mcsName.rbt";
    my $lineNum=0;
    while(<MCS>){
        chomp;
        if(/^:10/){
            my $length = length($_);
            my $startIndex = 9;
            die "$mcsName error: length not enough! lineNum: $lineNum." if($length<$startIndex);
            my $content = substr($_,$startIndex,$length-$startIndex-2);
            my $len = length($content);
            my $remain = $len%8;
            my $times = $len/8;
            die "$mcsName error: cannot divide by 8! lineNum: $lineNum." if($remain>0);
            #print "$content\n";
            my $rbtContent = &getMcsRbt($content,$times);
            print RBT $rbtContent;
        }
        $lineNum++;
    }
    close MCS;
    close RBT;
    &parseRbt("$mcsName.rbt");
}

sub getMcsRbt {
    my $str = shift;
    my $times = shift;
    my $rbt="";
    for(0..$times-1){
        my $substr = substr($str,$_*8,8);
        my $bin = &hex2bin($substr,8);
        $rbt .= "$bin\n";
    }
    return $rbt;
}

sub parseRbt{
    my $rbtName = shift;
    open RBT,"$rbtName" or die "cannot open $rbtName!";
    open OUT,">$rbtName.out" or die "cannot create $rbtName.log";
    my $currentState;
    $currentState->{packetType}=1;
    $currentState->{regName}="NONE";
    $currentState->{wordCount}=0;
    $currentState->{frame}=-1;
    while(<RBT>){
        chomp;
        if(/^[0,1]{32,}/){
            my $save = $_;
            $_ = &parseLine($_,$currentState);
        if($_){
                $_ = "$save\t$_";
            }else{
            $_ = $save;
        }
        }
        print OUT "$_\n";
    }
    close RBT;
    close OUT;
}

sub parseLine{
    my $line = shift;
    my $wordState = shift;
    my $packetType = $wordState->{packetType};
    my $regName = $wordState->{regName};
    my $word = $wordState->{wordCount};
    my $comment;
    if($packetType==1){
        if($regName eq "NONE"){
            if($line =~ /^1{32,}/ or $line =~ /^00111/){
                $comment="DUMMY";
            }elsif($line =~ /^10101010100110010101010101100110/){
                $comment = "SYNC WORD";
            }elsif($line =~ /^00000000000000000000000010111011/ or $line =~ /^00010001001000100000000001000100/){
                $comment = "BUS WIDTH AUTO DETECT";
            }elsif($line =~ /^00100/){
                $comment="NOP";
            }else{
                my ($reg,$word) = &getRegWord($line);
                $wordState->{regName}=$reg;
                $wordState->{wordCount}=$word;
                if($line =~ /^00110/){
                    $comment="Write";
                }elsif($line =~ /^00101/){
                    $comment="Read";
                }
                $comment .= " Reg:$reg, word:$word";
                if($reg eq "FDRI"){
                    $wordState->{packetType}=2;
                }elsif($reg eq "LOUT"){
                    $wordState->{packetType}=10;##need consider parser for ssi
                }
            }
        }else{
            $comment = &parseRegContent($regName,$line);
            if($wordState->{wordCount}==1){
                $wordState->{regName}="NONE";
                $wordState->{packetType}=1;
            }else{
                $wordState->{wordCount}=$wordState->{wordCount}-1;
            }
        }
    }elsif($packetType==2){
        if($word==0){
            my $wordBin = substr($line,5,27);
            my $wordDec = &bin2dec($wordBin,27);
            $wordState->{wordCount} = $wordDec;
            $comment = "Totalword:$wordDec";
        }else{
            my $wordDec = $wordState->{wordCount};
            $comment = &parseFDRIContent($line,$wordState);
            $wordState->{wordCount} = $wordDec-1;
            if($wordState->{wordCount}==0){
                $wordState->{packetType}=1;
                $wordState->{regName}="NONE";
            }
        }
    }elsif($packetType==10){
        if($word==0){
            my $wordBin = substr($line,5,27);
            my $wordDec = &bin2dec($wordBin,27);
            $wordState->{wordCount} = 0;
            $comment = "Totalword:$wordDec";
            if($wordState->{wordCount}==0){
                $wordState->{packetType}=1;
                $wordState->{regName}="NONE";
            }            
        }
    }
    return $comment;
}

sub getRegWord{
    my $line = shift;
    my $regAddr = substr($line,14,5);
    my $wordCountBin = substr($line,21,11);
    my $wordCount = &bin2dec($wordCountBin,11);
    my @regs = sort(keys %$registerHash);
    for my $reg(@regs){
        my $addr = $registerHash->{$reg}->{address};
        if($addr eq $regAddr){
            return ($reg,$wordCount);
        }
    }
    print "$line\n";
    print "Warning: not found $regAddr!\n";
    return ($regAddr,$wordCount);
}

##to do

sub parseFDRIContent{
    my $line = shift;
    my $wordState = shift;
    my $wordNum = $wordState->{wordCount};
    my $remain = $wordNum%101;
    my $comment = "";
    my $word = 101-$remain;
    if($remain==0){
        $wordState->{frame}=$wordState->{frame}+1;
        $comment = "frame:$wordState->{frame}";
        $word=0;
    }
    $comment .= " word:$word";
    return $comment;
    
}

##to do
sub parseRegContent{
    my $regName = shift;
    my $line = shift;
    my $comment = "";
    my $content;
    if($registerHash->{$regName}){
        $content = $registerHash->{$regName}->{content};
    }
    if($content){
        my @regItems = sort{$content->{$b}->{start}<=>$content->{$a}->{start}} keys %{$content};
        for my$item(@regItems){
            my $start = $content->{$item}->{start};
            my $len = $content->{$item}->{len};
            my $preValue = $content->{$item}->{value};
            my $cfgValue = substr($line,32-$start-$len,$len);
            if($preValue){
                my @keys = keys %$preValue;
                for my$key(@keys){
                    if($cfgValue eq $preValue->{$key}){
                        $comment .= "$item:$key ";
                        last;
                    }
                }
            }else{
                my$cfgValueDec = &bin2dec($cfgValue,$len);
                $comment .= "$item:$cfgValueDec ";
            }
        }
    }
    return "$comment";
}

sub getConfigReg{
    my $json = JSON->new();
    my $js;
    open REGFILE, "config_register_file";
    while(<REGFILE>) {
        next if(/^\s*#/);
        $js .= "$_";
    }
    my $obj = $json->decode($js);
    return $obj;
}

sub parseMsd{
    my $msdName = shift;
    open MSD,"$msdName" or die "cannot open $msdName!";
    open OUT,">$msdName.out" or die "cannot create $msdName.log";
    my $currentState;
    $currentState->{packetType}=2;
    $currentState->{regName}="NONE";
    $currentState->{wordCount}=$MAXNUM;
    $currentState->{frame}=-2;
    while(<MSD>){
        chomp;
        if(/^[0,1]{32,}/){
            my $save = $_;
            $_ = &parseLine($_,$currentState);
        if($_){
                $_ = "$save\t$_";
            }else{
            $_ = $save;
        }
        }
        print OUT "$_\n";
    }
    close MSD;
    close OUT;
}

sub parseRbd{
    my $rbdName = shift;
    open RBD,"$rbdName" or die "cannot open $rbdName!";
    open OUT,">$rbdName.out" or die "cannot create $rbdName.log";
    my $currentState;
    $currentState->{packetType}=2;
    $currentState->{regName}="NONE";
    $currentState->{wordCount}=$MAXNUM;
    $currentState->{frame}=-2;
    while(<RBD>){
        chomp;
        if(/^[0,1]{32,}/){
            my $save = $_;
            $_ = &parseLine($_,$currentState);
        if($_){
                $_ = "$save\t$_";
            }else{
            $_ = $save;
        }
        }
        print OUT "$_\n";
    }
    close RBD;
    close OUT;
}

sub bin2dec{
    my $bin = shift;
    my $bits = 32-shift;
    my $str = "0"x$bits;
    $str .= $bin;
    my $dec = unpack("N", pack("B32",$str));
    return $dec;
}

sub hex2bin{
    my $hex = shift;
    my $num = shift;
    my $totalBits = $num*4;
    my $dec = hex($hex);
    my $bin;
    $bin = sprintf("%0${totalBits}b",$dec);
    return $bin;
}