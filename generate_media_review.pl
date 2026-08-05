#!/usr/bin/perl
# generate_media_review.pl — Sailing Oroboro local media library
# Pre-installed on every macOS. Run from the site root:
#   perl generate_media_review.pl
# Also triggered automatically by .git/hooks/post-commit

use strict;
use warnings;
use File::Basename qw(basename dirname);
use POSIX qw();

my $SITE     = dirname( File::Spec->rel2abs($0) );
my $POSTS    = "$SITE/posts";
my $BLOG     = "$SITE/blog.html";
my $OUTPUT   = "$SITE/media-review.html";

# ── helpers ──────────────────────────────────────────────────────────────────
use File::Spec;

sub strip_tags {
    my ($s) = @_;
    $s =~ s/<[^>]+>//g;
    $s =~ s/&mdash;/—/g;  $s =~ s/&ndash;/-/g;
    $s =~ s/&amp;/&/g;    $s =~ s/&quot;/"/g;
    $s =~ s/&lt;/</g;     $s =~ s/&gt;/>/g;
    $s =~ s/&nbsp;/ /g;
    $s =~ s/\s+/ /g;
    $s =~ s/^\s+|\s+$//g;
    return $s;
}

sub esc {
    my ($s) = @_;
    $s =~ s/&/&amp;/g;
    $s =~ s/"/&quot;/g;
    $s =~ s/</&lt;/g;
    $s =~ s/>/&gt;/g;
    return $s;
}

# ── read blog.html for post order ────────────────────────────────────────────
my @order;   # list of slugs in blog order
my %meta;    # slug -> { region, date }

if (open my $fh, '<:utf8', $BLOG) {
    local $/; my $html = <$fh>; close $fh;
    while ($html =~ /href="\/posts\/([^"]+\.html)"[^>]*data-region="([^"]*)"/g) {
        my ($file, $region) = ($1, $2);
        (my $slug = $file) =~ s/\.html$//;
        push @order, $slug unless grep { $_ eq $slug } @order;
        # grab the date from the next 500 chars
        my $pos = pos($html) - length($&);
        my $snip = substr($html, $pos, 500);
        my $date = ($snip =~ /post-card-date">([^<]+)/) ? $1 : '';
        $date =~ s/^\s+|\s+$//g;
        $meta{$slug} = { region => $region, date => $date };
    }
}

# Add any posts not in blog.html
opendir my $dh, $POSTS or die "Cannot open posts/: $!";
my @extra = sort grep { /\.html$/ && do { (my $s=$_)=~s/\.html$//; !grep{$_ eq $s}@order } }
            readdir $dh;
closedir $dh;
push @order, map { (my $s=$_)=~s/\.html$//; $s } @extra;

# ── parse one post ────────────────────────────────────────────────────────────
sub parse_post {
    my ($slug) = @_;
    my $file = "$POSTS/$slug.html";
    return () unless -f $file;

    open my $fh, '<:utf8', $file or return ();
    local $/; my $html = <$fh>; close $fh;

    my $title = ($html =~ /<h1[^>]*>(.*?)<\/h1>/si) ? strip_tags($1) : $slug;
    $title =~ s/^\s+|\s+$//g;

    my @items;
    while ($html =~ /<figure[^>]*>(.*?)<\/figure>/gsi) {
        my $block = $1;
        my $caption = ($block =~ /<figcaption[^>]*>(.*?)<\/figcaption>/si) ? strip_tags($1) : '';

        # YouTube
        if ($block =~ /youtube\.com\/embed\/([A-Za-z0-9_-]+)/) {
            my $vid = $1;
            push @items, { kind => 'youtube',
                           thumb => "https://img.youtube.com/vi/$vid/hqdefault.jpg",
                           url   => "https://www.youtube.com/watch?v=$vid",
                           cap   => $caption };
            next;
        }

        # video with poster
        if ($block =~ /<video[^>]*poster="([^"]+)"/i) {
            my $poster = $1;
            my $src = ($block =~ /<source[^>]*src="([^"]+)"/i) ? $1 : '';
            push @items, { kind => 'video', thumb => $poster, url => $src, cap => $caption };
            next;
        }

        # img
        if ($block =~ /<img[^>]*src="([^"]+)"/i) {
            my $src = $1;
            next if $src =~ m{/img/|/images/posts/|logo|favicon}i;
            my $kind = ($src =~ m{/maps/|\.gif$}) ? 'map' : 'photo';
            push @items, { kind => $kind, thumb => $src, url => $src, cap => $caption };
        }
    }

    return { slug => $slug, title => $title, items => \@items,
             region => ($meta{$slug}{region} // ''),
             date   => ($meta{$slug}{date}   // '') };
}

# ── generate ──────────────────────────────────────────────────────────────────
print "Scanning posts...\n";

my @posts;
for my $slug (@order) {
    print "  $slug\n";
    my $p = parse_post($slug);
    push @posts, $p if $p && @{$p->{items}};
}

my $n_photo = 0; my $n_vid = 0; my $n_map = 0;
for my $p (@posts) {
    for my $it (@{$p->{items}}) {
        if    ($it->{kind} eq 'photo')                      { $n_photo++ }
        elsif ($it->{kind} eq 'video'||$it->{kind} eq 'youtube') { $n_vid++ }
        elsif ($it->{kind} eq 'map')                        { $n_map++ }
    }
}

print "Writing $OUTPUT...\n";
open my $out, '>:utf8', $OUTPUT or die "Cannot write $OUTPUT: $!";

print $out <<'HEAD';
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Oroboro Media Library</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0d1117;color:#e6edf3;font-family:system-ui,sans-serif}
.bar{position:sticky;top:0;z-index:50;background:#161b22;border-bottom:1px solid #30363d;
     padding:.65rem 1rem;display:flex;align-items:center;gap:.6rem;flex-wrap:wrap}
.bar h1{font-size:.9rem;font-weight:700;color:#58a6ff;white-space:nowrap}
.stats{font-size:.72rem;color:#8b949e;white-space:nowrap}
#q{flex:1;min-width:140px;max-width:260px;background:#0d1117;border:1px solid #30363d;
   border-radius:6px;color:#e6edf3;padding:.3rem .6rem;font-size:.8rem}
#q:focus{outline:none;border-color:#58a6ff}
.fbs{display:flex;gap:.35rem;flex-wrap:wrap}
.fb{background:#21262d;border:1px solid #30363d;border-radius:6px;color:#8b949e;
    font-size:.7rem;font-weight:700;letter-spacing:.05em;padding:.28rem .6rem;cursor:pointer}
.fb:hover{background:#30363d;color:#e6edf3}
.fb.on{background:#1f6feb;border-color:#1f6feb;color:#fff}
.wrap{padding:1.25rem 1rem;max-width:1600px;margin:0 auto}
.ps{margin-bottom:2.25rem}
.ph{display:flex;align-items:baseline;gap:.6rem;flex-wrap:wrap;
    margin-bottom:.75rem;padding-bottom:.45rem;border-bottom:1px solid #21262d}
.ph h2{font-size:.95rem;font-weight:700}
.ph h2 a{color:#58a6ff;text-decoration:none}
.ph h2 a:hover{text-decoration:underline}
.pm{font-size:.72rem;color:#8b949e}
.pc{font-size:.68rem;color:#6e7681;margin-left:auto}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(185px,1fr));gap:.45rem}
.item{background:#161b22;border-radius:6px;overflow:hidden;cursor:pointer;
      border:1px solid #21262d;transition:.15s}
.item:hover{border-color:#58a6ff;transform:scale(1.013);z-index:2;position:relative}
.item[hidden]{display:none}
.tw{position:relative;padding-top:75%;background:#0d1117;overflow:hidden}
.tw img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;
         opacity:0;transition:opacity .3s}
.tw img.show{opacity:1}
.play{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;pointer-events:none}
.kb{position:absolute;top:4px;right:4px;font-size:.58rem;font-weight:700;
    letter-spacing:.05em;padding:2px 5px;border-radius:4px}
.bp{background:rgba(31,111,235,.8);color:#fff}
.br{background:rgba(180,50,30,.85);color:#fff}
.bg{background:rgba(25,130,90,.85);color:#fff}
.cap{padding:.4rem .5rem;font-size:.67rem;line-height:1.4;color:#8b949e;
     background:#0d1117;border-top:1px solid #21262d}
#lb{display:none;position:fixed;inset:0;z-index:200;background:rgba(0,0,0,.92);
    flex-direction:column;align-items:center;justify-content:center;gap:.85rem;padding:1rem}
#lb.open{display:flex}
#lb img,#lb video{max-width:96vw;max-height:80vh;border-radius:6px;object-fit:contain}
#lb video{background:#000}
#lbc{color:#cdd9e5;font-size:.8rem;text-align:center;max-width:680px;line-height:1.5}
#lbx{position:fixed;top:.75rem;right:1rem;font-size:1.5rem;color:#8b949e;cursor:pointer}
#lbx:hover{color:#fff}
#lbn{position:fixed;top:50%;transform:translateY(-50%);display:flex;
     justify-content:space-between;width:100%;padding:0 .6rem;pointer-events:none}
.arr{pointer-events:all;background:rgba(255,255,255,.1);border:none;color:#fff;
     font-size:1.5rem;cursor:pointer;border-radius:50%;width:42px;height:42px;
     display:flex;align-items:center;justify-content:center}
.arr:hover{background:rgba(255,255,255,.25)}
</style>
</head>
<body>
HEAD

my $np = scalar @posts;
printf $out '<div class="bar"><h1>&#9875; Oroboro Media</h1>' .
            '<span class="stats">%d posts &middot; %d photos &middot; %d videos &middot; %d maps</span>' .
            '<input id="q" type="search" placeholder="Search captions&hellip;" autocomplete="off">' .
            '<div class="fbs">' .
            '<button class="fb on" data-k="all">All</button>' .
            '<button class="fb" data-k="photo">Photos</button>' .
            '<button class="fb" data-k="video">Videos</button>' .
            '<button class="fb" data-k="youtube">YouTube</button>' .
            '<button class="fb" data-k="map">Maps</button>' .
            '</div></div><div class="wrap">' . "\n",
            $np, $n_photo, $n_vid, $n_map;

for my $p (@posts) {
    my $slug   = $p->{slug};
    my $title  = esc($p->{title});
    my $region = esc($p->{region});
    my $date   = esc($p->{date});
    my $meta   = join(' &middot; ', grep { $_ } ($region, $date));
    my $n      = scalar @{$p->{items}};

    print $out qq{<section class="ps" id="s-$slug">} .
               qq{<div class="ph"><h2><a href="/posts/$slug.html" target="_blank">$title</a></h2>} .
               qq{<span class="pm">$meta</span><span class="pc">$n items</span></div>} .
               qq{<div class="grid">\n};

    for my $it (@{$p->{items}}) {
        my $kind  = $it->{kind};
        my $thumb = esc($it->{thumb});
        my $url   = esc($it->{url});
        my $cap   = esc($it->{cap});
        my $ptitle = esc($p->{title});

        my $bc = $kind eq 'photo' ? 'bp' : $kind eq 'map' ? 'bg' : 'br';
        my $bl = $kind eq 'youtube' ? 'YT' : $kind;
        my $play = ($kind eq 'video' || $kind eq 'youtube')
            ? '<div class="play"><svg width="38" height="38" viewBox="0 0 38 38">' .
              '<circle cx="19" cy="19" r="19" fill="rgba(0,0,0,.55)"/>' .
              '<polygon points="15,11 29,19 15,27" fill="white"/></svg></div>'
            : '';

        print $out
            qq{<div class="item" data-kind="$kind" data-url="$url" data-caption="$cap" data-post="$ptitle">} .
            qq{<div class="tw"><img data-src="$thumb" src="" alt="">$play} .
            qq{<span class="kb $bc">$bl</span></div>} .
            qq{<div class="cap">$it->{cap}</div></div>\n};
    }
    print $out "</div></section>\n";
}

print $out <<'FOOT';
</div>

<div id="lb">
  <span id="lbx" title="Close">&#x2715;</span>
  <img id="lbi" src="" alt="" hidden>
  <video id="lbv" controls hidden></video>
  <div id="lbc"></div>
  <div id="lbn">
    <button class="arr" id="lbp">&#8249;</button>
    <button class="arr" id="lbn2">&#8250;</button>
  </div>
</div>

<script>
const io=new IntersectionObserver(es=>{
  es.forEach(e=>{if(e.isIntersecting){const i=e.target;i.src=i.dataset.src;i.classList.add('show');io.unobserve(i);}});
},{rootMargin:'200px'});
document.querySelectorAll('img[data-src]').forEach(i=>io.observe(i));

const all=Array.from(document.querySelectorAll('.item'));
const secs=Array.from(document.querySelectorAll('.ps'));
let ak='all';
function run(){
  const q=document.getElementById('q').value.toLowerCase();
  all.forEach(el=>{
    const ok=(ak==='all'||el.dataset.kind===ak)&&
             (!q||el.dataset.caption.toLowerCase().includes(q)||el.dataset.post.toLowerCase().includes(q));
    el.hidden=!ok;
  });
  secs.forEach(s=>{
    const v=s.querySelectorAll('.item:not([hidden])').length;
    s.hidden=v===0;
    const c=s.querySelector('.pc');if(c)c.textContent=v?v+' shown':'';
  });
}
document.querySelectorAll('.fb').forEach(b=>b.addEventListener('click',()=>{
  document.querySelectorAll('.fb').forEach(x=>x.classList.remove('on'));
  b.classList.add('on');ak=b.dataset.k;run();
}));
document.getElementById('q').addEventListener('input',run);

const lb=document.getElementById('lb'),lbi=document.getElementById('lbi'),
      lbv=document.getElementById('lbv'),lbc=document.getElementById('lbc');
let li=[],lx=0;
function open2(x){
  const it=li[x];lx=x;
  lbi.hidden=true;lbv.hidden=true;lbv.pause&&lbv.pause();
  lbc.textContent=it.caption;
  if(it.kind==='video'){lbv.src=it.url;lbv.hidden=false;}
  else if(it.kind==='youtube'){lb.classList.remove('open');window.open(it.url,'_blank');return;}
  else{lbi.src=it.url;lbi.hidden=false;}
  lb.classList.add('open');
}
function close2(){lb.classList.remove('open');lbv.pause&&lbv.pause();}
all.forEach(el=>el.addEventListener('click',()=>{
  li=all.filter(e=>!e.hidden).map(e=>({kind:e.dataset.kind,url:e.dataset.url,caption:e.dataset.caption}));
  const idx=li.findIndex(i=>i.url===el.dataset.url&&i.caption===el.dataset.caption);
  open2(Math.max(0,idx));
}));
document.getElementById('lbx').onclick=close2;
lb.addEventListener('click',e=>{if(e.target===lb)close2();});
document.getElementById('lbp').onclick=e=>{e.stopPropagation();if(lx>0)open2(lx-1);};
document.getElementById('lbn2').onclick=e=>{e.stopPropagation();if(lx<li.length-1)open2(lx+1);};
document.addEventListener('keydown',e=>{
  if(!lb.classList.contains('open'))return;
  if(e.key==='Escape')close2();
  if(e.key==='ArrowLeft'&&lx>0)open2(lx-1);
  if(e.key==='ArrowRight'&&lx<li.length-1)open2(lx+1);
});
</script>
</body>
</html>
FOOT

close $out;

my $total = 0; $total += scalar @{$_->{items}} for @posts;
my $kb = int(-s $OUTPUT / 1024);
printf "Done — %d posts, %d items, %d KB\n", scalar @posts, $total, $kb;
