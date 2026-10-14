# frozen_string_literal: true

# This plugin's tests, run with `trmnlp test` (add `--report report` for a page of every screen it drew).
# Docs: https://github.com/usetrmnl/trmnlp#testing-plugins
RSpec.describe 'Picture of the Day' do
  def commons(image, caption)
    {
      'https://commons.wikimedia.org/w/api.php?*generator=images*' =>
        { json: JSON.parse(File.read(File.join(__dir__, "fixtures/#{image}.json"))) },
      'https://commons.wikimedia.org/w/api.php?*prop=revisions*' =>
        { json: JSON.parse(File.read(File.join(__dir__, "fixtures/#{caption}.json"))) }
    }
  end

  let(:custom_fields) { { 'language' => 'de' } }

  # Real Commons responses, captions in German and English.
  context 'with a tall picture (2026-10-12)' do
    let(:mocks) { commons('commons_image', 'commons_caption') }

    # Every view on TRMNL's devices, a failing API and every select option, checked for page errors and leaked values.
    it_behaves_like 'a publishable recipe'
  end

  context 'with a wide picture (2026-10-11)' do
    let(:mocks) { commons('commons_image_wide', 'commons_caption_wide') }

    it_behaves_like 'a publishable recipe'
  end

  # Before Commons publishes the day's picture: the empty state, on every view and screen.
  context 'without a picture yet' do
    let(:mocks) { { 'https://commons.wikimedia.org/w/api.php?*' => { json: {} } } }

    it_behaves_like 'a publishable recipe'

    %w[full half_horizontal half_vertical quadrant].each do |view|
      it "says so in the #{view} view on TRMNL X in portrait" do
        screen = trmnl.render(view:, device: 'v2', orientation: :portrait, mocks:, custom_fields:)
        expect(screen).to have_text('Today’s picture isn’t out yet')
      end
    end
  end

  # The English caption of 2026-10-12 is long: its title may grow, but not past the lines it can show.
  context 'with a long English caption' do
    let(:mocks) { commons('commons_image', 'commons_caption_en') }
    let(:custom_fields) { { 'language' => 'en' } }

    it_behaves_like 'a publishable recipe'

    %w[og_plus v2].each do |device|
      it "shows the whole caption in the full view on #{device}" do
        screen = trmnl.render(view: 'full', device:, mocks:, custom_fields:)
        expect(screen.evaluate("(t => t.scrollHeight <= t.clientHeight + 1)(document.querySelector('.poty__title'))"))
          .to be true
      end
    end
  end
end
